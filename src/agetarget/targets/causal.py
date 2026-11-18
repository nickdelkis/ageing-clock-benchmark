"""Causal evidence from Mendelian randomisation (the R scripts in mr/), read from results/mr/.

The R scripts in mr/ write:
    mr_exposures.csv             protein, pQTL study, instruments genome-wide and in the cis window
    mr_instruments.csv           cis instruments with F-statistics
    mr_results.csv               MR estimates per protein x outcome x method, direction, Bonferroni p
    mr_checks.csv                heterogeneity and Egger intercept, where there were enough variants
    replication_<rsid>.csv       the instrument looked up in other studies of the same protein
    coloc_<PROTEIN>_<outcome>.csv  colocalisation summary
    phewas_<rsid>.csv            other traits associated with the instrument

load() turns these into short, citable facts per protein (fact ids start with "causal."),
which the agent reads through the get_causal_evidence tool.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NOT_PROVIDED = {
    "causal.mr_status": "not tested: no Mendelian randomisation results were provided for this target",
}


def _p(p) -> str:
    p = float(p)
    return f"{p:.1e}" if p < 1e-3 else f"{p:.2g}"


def _true(s: pd.Series) -> pd.Series:
    return s.astype(str).str.upper().isin(["TRUE", "1"])


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _outcome_coding(res: pd.DataFrame) -> list[str]:
    signs = res.drop_duplicates("outcome").set_index("outcome").harmful_sign
    return [f"{o}: {'positive' if s > 0 else 'negative'} b means worse ageing" for o, s in signs.items()]


def _mr_facts(protein: str, res: pd.DataFrame, n_tests: int) -> dict:
    primary = res[_true(res.primary)].sort_values("pval")
    lines, significant, directions = [], [], set()
    for _, r in primary.iterrows():
        sig = pd.notna(r.p_bonferroni) and r.p_bonferroni < 0.05
        # Only a significant estimate suggests a modulation direction; otherwise give the sign alone
        note = r.direction if sig else r.direction.split(" (")[0] + " (point estimate only, not significant)"
        lines.append(f"{r.outcome}: {r.method}, {int(r.nsnp)} variant(s), b = {r.b:+.3f} (SE {r.se:.3f}), "
                     f"p = {_p(r.pval)}, Bonferroni p = {_p(r.p_bonferroni)}; {note}")
        if sig:
            significant.append(r.outcome)
            directions.add(r.direction)
    if not significant:
        summary = "no Bonferroni-significant effect on any outcome"
    elif len(directions) == 1:
        summary = directions.pop()
    else:
        summary = "conflicting directions across outcomes"
    other = res[~_true(res.primary)]
    sensitivity = [f"{r.outcome}: {r.method}, b = {r.b:+.3f}, p = {_p(r.pval)}" for _, r in other.iterrows()]
    return {
        "causal.mr_results": lines,
        "causal.mr_significant_outcomes": significant,
        "causal.mr_direction": summary,
        "causal.mr_n_tests_corrected": n_tests,
        "causal.mr_sensitivity": sensitivity,
    }


def _checks(protein: str, checks: pd.DataFrame | None) -> list[str]:
    if checks is None or "protein" not in checks:
        return []
    out = []
    for _, r in checks[checks.protein == protein].iterrows():
        if "Q_pval" in r and pd.notna(r.get("Q_pval")):
            out.append(f"{r.outcome}: heterogeneity ({r.method}) Q p = {_p(r.Q_pval)}")
        if "egger_intercept" in r and pd.notna(r.get("egger_intercept")):
            out.append(f"{r.outcome}: Egger intercept {r.egger_intercept:+.4f}, p = {_p(r.pval)}")
    return out


def _replication(protein: str, rep: pd.DataFrame, ref_allele: dict[str, str], exposure_id: str) -> list[str]:
    # The MR exposure dataset is the discovery, not a replication; the instrument facts already describe it
    rep = rep[(rep.protein == protein) & (rep.id != exposure_id)].sort_values("p")
    # Some datasets hold duplicate rows for a variant; keep the strongest, as in the colocalisation script
    rep = rep.drop_duplicates(["study", "rsid"])
    out = []
    for _, r in rep.iterrows():
        allele, beta = r.ea, r.beta
        ref = ref_allele.get(r.rsid)
        if ref and r.ea != ref and r.nea == ref:     # express every effect for the same allele
            allele, beta = ref, -beta
        label = r.study + (" (DNA-methylation surrogate, not the measured protein)" if r.measure != "protein" else "")
        out.append(f"{label}: {r.rsid} allele {allele} beta = {beta:+.3f}, p = {_p(r.p)}")
    return out


def _coloc(protein: str, coloc_rows: list[pd.Series]) -> list[str]:
    out = []
    for r in coloc_rows:
        if r.protein != protein:
            continue
        out.append(f"{r.outcome} (+/-{int(r.flank_kb)} kb, {int(r.nsnps)} variants): PP.H4 = {r['PP.H4.abf']:.2f}, "
                   f"PP.H3 = {r['PP.H3.abf']:.2f}, PP.H1 = {r['PP.H1.abf']:.2f}, PP.H2 = {r['PP.H2.abf']:.2f}; "
                   f"most likely shared variant {r.top_snp} (SNP.PP.H4 = {r.top_snp_pp_h4:.2f}); "
                   f"strongest outcome variant {r.outcome_top_snp}, {r.outcome_top_kb:+.0f} kb from the gene, "
                   f"p = {_p(r.outcome_min_p)}")
    return out


def _phewas(path: Path, n_top: int = 10) -> dict:
    ph = pd.read_csv(path)
    is_eqtl = ph.id.astype(str).str.startswith("eqtl-")
    top = ph[~is_eqtl].sort_values("p").drop_duplicates("trait").head(n_top)
    return {
        "causal.phewas_counts": f"{len(ph)} associations at p < 1e-5, of which {int(is_eqtl.sum())} are gene-expression (eQTL) traits",
        "causal.phewas_top_traits": [f"{r.trait} (p = {_p(r.p)})" for _, r in top.iterrows()],
    }


def load(results_dir: str | Path) -> dict[str, dict]:
    """protein symbol -> causal facts. Returns {} if the MR scripts have not been run."""
    d = Path(results_dir)
    exposures = _read(d / "mr_exposures.csv")
    if exposures is None:
        return {}
    res = _read(d / "mr_results.csv")
    instr = _read(d / "mr_instruments.csv")
    checks = _read(d / "mr_checks.csv")
    coloc_rows = [row for f in sorted(d.glob("coloc_*.csv")) for _, row in pd.read_csv(f).iterrows()
                  if "protein" in row]
    rep = pd.concat([pd.read_csv(f) for f in sorted(d.glob("replication_*.csv"))], ignore_index=True) \
        if any(d.glob("replication_*.csv")) else None

    n_tests = int(_true(res.primary).sum()) if res is not None else 0
    ref_allele = dict(zip(instr.SNP, instr["effect_allele.exposure"])) if instr is not None else {}

    out = {}
    for _, e in exposures.iterrows():
        protein = e.protein
        if pd.isna(e.exposure_id):
            out[protein] = {"causal.mr_status": "not tested: no pQTL dataset chosen"}
            continue
        f = {"causal.exposure_study": e.study}
        if e.n_cis == 0:
            f["causal.mr_status"] = (f"not tested: no cis instruments (p < 5e-8 within 1 Mb of the gene; "
                                     f"{int(e.n_genome_wide)} genome-wide). Untested is not a null result.")
            out[protein] = f
            continue
        mine = instr[instr.exposure == protein]
        f["causal.mr_status"] = f"tested: {len(mine)} cis instrument(s)"
        f["causal.instruments"] = [f"{r.SNP} (F = {r.F_stat:.0f})" for _, r in mine.iterrows()]
        mr = res[res.protein == protein] if res is not None else pd.DataFrame()
        if mr.empty:
            f["causal.mr_status"] += "; no outcome results"
            out[protein] = f
            continue
        f["causal.outcome_coding"] = _outcome_coding(mr)
        f.update(_mr_facts(protein, mr, n_tests))
        f["causal.mr_checks"] = _checks(protein, checks)
        f["causal.colocalisation"] = _coloc(protein, coloc_rows)
        f["causal.replication"] = _replication(protein, rep, ref_allele, e.exposure_id) if rep is not None else []
        for snp in mine.SNP:
            if (d / f"phewas_{snp}.csv").exists():
                f.update(_phewas(d / f"phewas_{snp}.csv"))
        out[protein] = f
    return out


def attach(dossiers: dict[str, dict], results_dir: str | Path) -> dict[str, dict]:
    """Add each target's causal facts to its dossier in memory (not to the cached evidence JSON)."""
    loaded = load(results_dir)
    for symbol, dossier in dossiers.items():
        dossier["causal"] = loaded.get(symbol, NOT_PROVIDED)
    return loaded
