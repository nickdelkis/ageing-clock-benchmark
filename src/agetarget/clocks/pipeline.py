"""The clock analysis, end to end: one cohort at a time, then pooled across cohorts.

run_cohort() writes to results/clocks/<cohort>/:
    samples.csv                  every sample: group, age, sex, smoking score, blood cells, QC status
    clock_estimates.csv          each clock's raw estimate
    age_deviation_per_sample.csv residual of each clock on chronological age
    clock_metrics.csv            agreement with chronological age
    age_deviation_correlations.csv
    case_control.csv             schizophrenia vs control, adjusted for sex, all samples
    case_control_adjusted.csv    the same under three nested covariate models, all and QC-passed samples
    cohens_d_by_sample_set.csv   how the unadjusted effect depends on the QC exclusions
    probe_sensitivity_*.csv      the clocks rerun on another cohort's probe set
    summary.json, environment.txt, and the figures
pool() combines the cohorts' case_control_adjusted.csv into results/clocks/pooled/.
"""

from __future__ import annotations

import gc
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from .. import config as cfg
from ..style import apply_style
from . import data as geo, models
from .plots import plot_adjustment_effect, plot_deviation_heatmap, plot_group_forest, plot_predicted_vs_age
from .stats import clock_metrics, compare_groups, deviation_correlations, deviation_table, meta_analyse

SEX_LABELS = {1: "Male", 0: "Female"}


# ---- QC steps, kept small so they can be tested without Biolearn ---------------


def unusable_ages(age: pd.Series, age_range: tuple[float, float] = cfg.AGE_RANGE) -> tuple[pd.Index, pd.Series]:
    """Samples without a usable age: missing, or outside the plausible range (returned separately)."""
    age = pd.to_numeric(age, errors="coerce")
    implausible = age[(age < age_range[0]) | (age > age_range[1])]
    return age.index[age.isna()].union(implausible.index), implausible


def sex_check_possible(coverage: dict[str, float], minimum: dict[str, float] = cfg.SEX_CHECK_MIN) -> bool:
    return all(coverage[k] >= minimum[k] for k in minimum)


def sample_status(index: pd.Index, no_age, sex_mismatch, manual) -> pd.Series:
    """One QC status per sample; the first reason that applies wins."""
    status = pd.Series("QC-passed", index=index, name="status")
    status[status.index.isin(manual)] = "manual exclusion"
    status[status.index.isin(sex_mismatch)] = "sex mismatch"
    status[status.index.isin(no_age)] = "no usable age"
    return status


def adjusted_effects(preds: pd.DataFrame, age: pd.Series, groups: pd.Series, covariates: dict[str, list],
                     sample_sets: dict[str, pd.Index]) -> pd.DataFrame:
    """Case minus control in age deviation, per clock, covariate model and sample set.

    Age deviations are refitted within each sample set, so excluded samples do not shape the residuals.
    """
    rows = []
    for sample_set, keep in sample_sets.items():
        dev = deviation_table(preds.loc[keep], age.loc[keep])
        for name, parts in covariates.items():
            r = compare_groups(dev, groups, cfg.CASE, cfg.CONTROL, covariates=pd.concat(parts, axis=1))
            rows.append(r[["n_case", "n_control", "diff_adjusted", "se_adjusted", "p_adjusted"]]
                        .assign(samples=sample_set, model=name).reset_index())
    return pd.concat(rows, ignore_index=True)


def _save(fig, path: Path) -> None:
    fig.savefig(path)
    plt.close(fig)


def _environment(path: Path, dataset: str) -> None:
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    path.write_text(f"dataset={dataset}\nimputation={cfg.IMPUTATION}\n\n" + freeze)


# ---- One cohort ---------------------------------------------------------------


def run_cohort(dataset: str, out: Path | None = None, log: Callable[[str], None] = print) -> dict:
    """Clocks, QC, case-control comparisons and the probe-set sensitivity check for one cohort."""
    apply_style()
    out = Path(out or cfg.CLOCK_RESULTS / dataset)
    out.mkdir(parents=True, exist_ok=True)
    summary: dict = {"dataset": dataset, "imputation": cfg.IMPUTATION}

    # -- data and ages
    data = geo.load_dataset(dataset)
    age_col = geo.find_column(data.metadata, "age")
    sex_col = geo.find_column(data.metadata, "sex", "gender")
    loaded = data.metadata.copy()
    no_age, implausible = unusable_ages(loaded[age_col])
    for sample, value in implausible.items():
        log(f"Recorded age {value:g} for {sample} is outside {cfg.AGE_RANGE}: treated as missing")
    if len(no_age):
        by_group = loaded.loc[no_age, "disease"].map(cfg.DISEASE_LABELS).value_counts().to_dict()
        log(f"Dropped {len(no_age)} samples without a usable age: {by_group}")
        data = geo.subset_samples(data, data.metadata.index.difference(no_age))
    summary.update(n_loaded=len(loaded), n_no_usable_age=len(no_age),
                   implausible_ages={k: float(v) for k, v in implausible.items()}, cpgs=int(data.dnam.shape[0]))

    meta = data.metadata.copy()
    age = pd.to_numeric(meta[age_col], errors="coerce")
    sex01 = meta[sex_col].astype(float).rename("sex")
    groups = meta["disease"].map(cfg.DISEASE_LABELS).astype("string")
    log(f"{dataset}: {data.dnam.shape[0]:,} CpGs x {data.dnam.shape[1]} samples; "
        f"{groups.value_counts().to_dict()}; age {age.min():.0f}-{age.max():.0f}, median {age.median():.0f}")

    # -- clocks, on just the CpGs the models read
    clock_names = {label: name for label, (name, _) in cfg.CLOCKS.items()}
    model_input = geo.subset_cpgs(data, models.model_cpgs(list(clock_names.values()) + [cfg.SMOKING_MODEL, cfg.CELL_MODEL]))
    summary["model_input_cpgs"] = int(model_input.dnam.shape[0])
    run = models.run_clocks(model_input, clock_names)
    for label, err in run.failed.items():
        log(f"  {label} FAILED: {err[:160]}")
    summary["clocks_failed"] = run.failed
    preds = run.predictions
    kinds = {label: kind for label, (_, kind) in cfg.CLOCKS.items() if label in preds.columns}
    preds.to_csv(out / "clock_estimates.csv")
    dev = deviation_table(preds, age)
    dev.to_csv(out / "age_deviation_per_sample.csv")

    # -- sex check, on the full matrix
    coverage = models.sex_probe_coverage(data.dnam)
    recorded = meta[sex_col].map(SEX_LABELS)
    sex_mismatch: list[str] = []
    predicted = pd.Series(None, index=meta.index, dtype=object, name="predicted_sex")
    if sex_check_possible(coverage):
        predicted = models.predicted_sex(data)["predicted_sex"].reindex(meta.index)
        sex_mismatch = meta.index[predicted.notna() & (predicted != recorded)].tolist()
        log(f"Sex check: {len(sex_mismatch)} mismatches of {len(meta)}")
    else:
        log("Sex check skipped: too few of the estimator's X/Y probes")
    summary["sex_check"] = {"probe_coverage": coverage, "ran": sex_check_possible(coverage),
                            "mismatches": sex_mismatch}
    del data
    gc.collect()

    # -- QC
    manual = cfg.COHORTS.get(dataset, {}).get("exclude", [])
    qc_fail = sex_mismatch + [s for s in manual if s not in sex_mismatch]
    qc_pass = meta.index.difference(qc_fail)
    summary.update(manual_exclusions=manual, n_qc_passed=len(qc_pass),
                   most_negative_deviation={c: [dev[c].idxmin(), round(float(dev[c].min()), 1)] for c in dev})
    log(f"QC-passed samples: {len(qc_pass)} (excluded: {', '.join(qc_fail) or 'none'})")

    # -- covariates
    smoking = models.smoking_score(model_input)
    cells = models.cell_proportions(model_input)
    cellcov = cells[cfg.CELL_COVARIATES]

    samples = pd.DataFrame({
        "group": loaded["disease"].map(cfg.DISEASE_LABELS),
        "age": pd.to_numeric(loaded[age_col], errors="coerce"),
        "sex": loaded[sex_col].map(SEX_LABELS),
        "predicted_sex": predicted,
        "smoking": smoking,
    }).join(cells).join(sample_status(loaded.index, no_age, sex_mismatch, manual))
    samples.index.name = "sample"
    samples.to_csv(out / "samples.csv")

    # -- agreement with age, and between clocks
    metrics = clock_metrics(preds, age, kinds)
    metrics.to_csv(out / "clock_metrics.csv")
    _save(plot_predicted_vs_age(preds, age, kinds, metrics=metrics, groups=groups,
                                group_order=[cfg.CONTROL, cfg.CASE]), out / "predicted_vs_age.png")
    corr = deviation_correlations(dev, method="spearman")
    corr.to_csv(out / "age_deviation_correlations.csv")
    _save(plot_deviation_heatmap(corr), out / "deviation_correlation.png")

    # -- schizophrenia vs control
    res = compare_groups(dev, groups, case=cfg.CASE, control=cfg.CONTROL, covariates=sex01.to_frame())
    res.to_csv(out / "case_control.csv")
    _save(plot_group_forest(res, case=cfg.CASE, control=cfg.CONTROL), out / "case_control_effect.png")

    sample_sets = {"all": meta.index, "without outlier": meta.index.difference(manual), "QC-passed": qc_pass}
    pd.DataFrame({
        name: compare_groups(deviation_table(preds.loc[keep], age.loc[keep]), groups, cfg.CASE, cfg.CONTROL)["cohens_d"]
        for name, keep in sample_sets.items()
    }).to_csv(out / "cohens_d_by_sample_set.csv")

    covariates = {"sex": [sex01], "sex+smoking": [sex01, smoking], "sex+smoking+cells": [sex01, smoking, cellcov]}
    adjusted = adjusted_effects(preds, age, groups, covariates,
                                {"all": sample_sets["all"], "QC-passed": sample_sets["QC-passed"]})
    adjusted.to_csv(out / "case_control_adjusted.csv", index=False)

    d_sd = deviation_table(preds.loc[qc_pass], age.loc[qc_pass])
    d_sd = d_sd / d_sd.std()
    effects = {cfg.COVARIATE_MODELS[name]: compare_groups(d_sd, groups, cfg.CASE, cfg.CONTROL,
                                                          covariates=pd.concat(parts, axis=1))
               for name, parts in covariates.items()}
    order = [c for c in cfg.CLOCK_ORDER if c in d_sd.columns]
    n_case, n_ctrl = (int(v) for v in effects["Sex"].loc[order[0], ["n_case", "n_control"]])
    _save(plot_adjustment_effect(
        effects, order,
        title="Schizophrenia vs control on each clock, before and after adjustment",
        subtitle=f"{dataset}, QC-passed samples ({n_case} cases, {n_ctrl} controls). Each colour adds covariates to the model.",
        xlabel="Schizophrenia minus control: age deviation in SD units (95% CI)",
        highlight=cfg.HIGHLIGHT,
    ), out / "adjustment_effect.png")

    # -- probe-set sensitivity
    probes = cfg.SENSITIVITY_PROBES
    if probes and probes != dataset:
        probe_sensitivity(model_input, preds, age.loc[qc_pass], groups, sex01, smoking, clock_names, probes,
                          dataset, out, log)

    summary["n"] = {name: {k: int(v) for k, v in groups.loc[keep].value_counts().items()}
                    for name, keep in [("all", meta.index), ("QC-passed", qc_pass)]}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    _environment(out / "environment.txt", dataset)
    log(f"Wrote {out}")
    return summary


def probe_sensitivity(model_input, preds, age_qc, groups, sex01, smoking, clock_names, probes, dataset, out, log):
    """Rerun the clocks on only another cohort's probes; compare estimates and the schizophrenia effect."""
    restricted = geo.subset_cpgs(model_input, geo.probe_ids(probes))
    log(f"Probe-set sensitivity: {model_input.dnam.shape[0] - restricted.dnam.shape[0]:,} of "
        f"{model_input.dnam.shape[0]:,} model CpGs are not in {probes}")
    run_r = models.run_clocks(restricted, clock_names)
    smoking_r = models.smoking_score(restricted)

    qc_pass = age_qc.index
    both = [c for c in preds.columns if c in run_r.predictions.columns]
    full_p, restr_p = preds.loc[qc_pass, both], run_r.predictions.loc[qc_pass, both]
    dev_full = deviation_table(full_p, age_qc)
    dev_restr = deviation_table(restr_p, age_qc)
    pd.DataFrame({
        "r, estimate": full_p.corrwith(restr_p),
        "r, age deviation": dev_full.corrwith(dev_restr),
        "mean shift": (restr_p - full_p).mean(),
        "SD ratio, age deviation": dev_restr.std() / dev_full.std(),
    }).to_csv(out / f"probe_sensitivity_agreement_{probes}.csv")

    scale = dev_full.std()   # both in SD units of the all-probe deviation, so shrinkage shows
    label = f"{probes} probes only"
    sens = {}
    for probe_set, d, smk in [("all probes", dev_full / scale, smoking), (label, dev_restr / scale, smoking_r)]:
        for model, cov in [("sex", sex01.to_frame()), ("sex+smoking", pd.concat([sex01, smk], axis=1))]:
            sens[(probe_set, model)] = compare_groups(d, groups, cfg.CASE, cfg.CONTROL, covariates=cov)
    pd.concat({k: v[["diff_adjusted", "p_adjusted"]] for k, v in sens.items()}, axis=1) \
        .to_csv(out / f"probe_sensitivity_effects_{probes}.csv")

    order = [c for c in cfg.CLOCK_ORDER if c in both]
    n_case, n_ctrl = (int(v) for v in sens[("all probes", "sex")].loc[order[0], ["n_case", "n_control"]])
    _save(plot_adjustment_effect(
        {"All probes": sens[("all probes", "sex")], label: sens[(label, "sex")]}, order,
        title=f"How much {probes}'s missing probes change the schizophrenia effect",
        subtitle=f"{dataset}, QC-passed samples ({n_case} cases, {n_ctrl} controls), adjusted for sex.",
        xlabel="Schizophrenia minus control: SD units of the all-probe age deviation (95% CI)",
        highlight=cfg.HIGHLIGHT,
    ), out / f"probe_sensitivity_{probes}.png")


# ---- Pooled across cohorts ----------------------------------------------------


def pool(cohorts: list[str] | None = None, out: Path | None = None, samples: str = "QC-passed",
         log: Callable[[str], None] = print) -> pd.DataFrame:
    """Random-effects meta-analysis of each clock's schizophrenia effect, per covariate model."""
    apply_style()
    cohorts = cohorts or list(cfg.COHORTS)
    out = Path(out or cfg.CLOCK_RESULTS / "pooled")
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for gse in cohorts:
        df = pd.read_csv(cfg.CLOCK_RESULTS / gse / "case_control_adjusted.csv")
        frames.append(df[df["samples"] == samples].assign(cohort=gse))
    per_cohort = pd.concat(frames, ignore_index=True)

    rows = []
    for (clock, model), g in per_cohort.groupby(["clock", "model"]):
        m = meta_analyse(g["diff_adjusted"], g["se_adjusted"])
        rows.append({"clock": clock, "model": model, "n_case": g["n_case"].sum(), "n_control": g["n_control"].sum(), **m})
    pooled = pd.DataFrame(rows).set_index(["clock", "model"])
    pooled.to_csv(out / "pooled_effects.csv")

    label = "Pooled (random effects)"
    for clock in ["GrimAge2", "DunedinPACE"]:
        effects = {}
        for model, model_label in cfg.COVARIATE_MODELS.items():
            g = per_cohort[(per_cohort["clock"] == clock) & (per_cohort["model"] == model)].set_index("cohort")
            tbl = g[["diff_adjusted", "se_adjusted"]].copy()
            tbl.index = [f"{c} ({g.loc[c, 'n_case']} cases / {g.loc[c, 'n_control']} controls)" for c in g.index]
            p = pooled.loc[(clock, model)]
            # The plot draws estimate +/- 1.96 SE, so give the pooled row the SE that reproduces its HKSJ interval
            tbl.loc[label] = [p["random"], (p["hk_ci_high"] - p["random"]) / 1.96]
            effects[model_label] = tbl
        _save(plot_adjustment_effect(
            effects, [label] + [r for r in reversed(tbl.index) if r != label],
            title=f"{clock}: schizophrenia effect in three cohorts, before and after adjustment",
            subtitle="QC-passed samples. Cohorts with 95% CI; pooled random-effects estimate with Hartung-Knapp 95% CI.",
            xlabel=f"Schizophrenia minus control ({cfg.UNITS.get(clock, 'years')})",
            highlight={label},
        ), out / f"pooled_{clock}.png")
    log(f"Pooled {len(cohorts)} cohorts -> {out}")
    return pooled
