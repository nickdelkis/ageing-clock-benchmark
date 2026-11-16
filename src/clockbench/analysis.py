"""Statistics for comparing ageing clocks.

Terminology follows Moqri et al. 2023 (Cell): the gap between a clock's
estimate and chronological age is the *age deviation* (AgeDev). Two kinds of
clock are handled:

- "age" clocks estimate biological age in years (Horvath, Hannum, PhenoAge,
  GrimAge, causal clocks). These are odometers.
- "pace" clocks estimate the current rate of ageing (DunedinPACE, ~1.0 =
  one biological year per calendar year). These are speedometers and are not
  meant to track chronological age.

All functions take pandas objects indexed by sample ID and align on that index.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

AGE = "age"
PACE = "pace"


def _aligned(predicted: pd.Series, age: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Align two series on sample ID and drop samples missing either value."""
    df = pd.concat({"pred": predicted, "age": age}, axis=1, join="inner").dropna()
    if len(df) < 3:
        raise ValueError(f"Need at least 3 samples with both values, got {len(df)}.")
    return df["pred"].astype(float), df["age"].astype(float)


def age_deviation(predicted: pd.Series, age: pd.Series, method: str = "residual") -> pd.Series:
    """Age deviation per sample.

    method="residual" (default): residual of the clock regressed on
        chronological age. Removes the clock's systematic bias (most clocks
        over-predict the young and under-predict the old), so the deviation is
        uncorrelated with age within this dataset. This is the usual
        "age acceleration residual" and is the right choice for comparing
        clocks or groups. It also works for pace clocks.
    method="raw": predicted minus chronological age, Moqri's literal AgeDev.
        Only meaningful for age clocks, and confounded by the clock's bias.
    """
    pred, chron = _aligned(predicted, age)
    if method == "raw":
        return (pred - chron).rename(predicted.name)
    if method != "residual":
        raise ValueError("method must be 'residual' or 'raw'")
    slope, intercept, *_ = stats.linregress(chron, pred)
    return (pred - (intercept + slope * chron)).rename(predicted.name)


def clock_metrics(predictions: pd.DataFrame, age: pd.Series, kinds: Mapping[str, str]) -> pd.DataFrame:
    """One row per clock: agreement with chronological age.

    For age clocks: Pearson r, mean absolute error (years), median absolute
    error and mean bias (predicted - chronological). For pace clocks only r is
    reported; error in years is meaningless for a rate.

    A high r and low MAE is *not* the goal of a good ageing biomarker (the
    "paradox of biomarkers"); this table is context for the other analyses.
    """
    rows = []
    for clock in predictions.columns:
        pred, chron = _aligned(predictions[clock], age)
        kind = kinds.get(clock, AGE)
        row = {
            "clock": clock,
            "kind": kind,
            "n": len(pred),
            "pearson_r": stats.pearsonr(chron, pred)[0],
        }
        if kind == AGE:
            err = pred - chron
            row.update(
                mae_years=err.abs().mean(),
                median_ae_years=err.abs().median(),
                mean_bias_years=err.mean(),
            )
        else:
            row.update(mae_years=np.nan, median_ae_years=np.nan, mean_bias_years=np.nan)
        rows.append(row)
    return pd.DataFrame(rows).set_index("clock")


def deviation_table(predictions: pd.DataFrame, age: pd.Series) -> pd.DataFrame:
    """Residual age deviation for every clock, samples x clocks."""
    devs = {c: age_deviation(predictions[c], age) for c in predictions.columns}
    return pd.DataFrame(devs)


def deviation_correlations(deviations: pd.DataFrame, method: str = "spearman") -> pd.DataFrame:
    """Pairwise correlation of age deviations between clocks.

    Low correlations mean the clocks disagree about *who* is ageing fast,
    even when they all track chronological age well.
    """
    return deviations.corr(method=method)


def bh_adjust(pvalues: Sequence[float]) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaNs are kept as NaN)."""
    p = np.asarray(pvalues, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    if not ok.any():
        return out
    q = p[ok]
    n = len(q)
    order = np.argsort(q)
    ranked = q[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adj = np.empty(n)
    adj[order] = np.clip(ranked, 0, 1)
    out[ok] = adj
    return out


def _ols_group_effect(y: np.ndarray, group: np.ndarray, covariates: np.ndarray | None):
    """Coefficient, SE and p-value for `group` in y ~ 1 + group + covariates."""
    cols = [np.ones_like(y), group]
    if covariates is not None and covariates.size:
        cols.extend(covariates.T)
    X = np.column_stack(cols)
    dof = len(y) - X.shape[1]
    if dof < 1:
        return np.nan, np.nan, np.nan
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sigma2 = resid @ resid / dof
    cov = sigma2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(cov[1, 1])
    t = beta[1] / se
    p = 2 * stats.t.sf(abs(t), dof)
    return beta[1], se, p


def compare_groups(
    deviations: pd.DataFrame,
    groups: pd.Series,
    case: str,
    control: str,
    covariates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Case vs control difference in age deviation, per clock.

    Reports, per clock:
      - mean deviation in each group and the difference (case - control),
        in the clock's own units (years, or pace units for pace clocks);
      - Cohen's d with an approximate 95% CI, so clocks on different scales
        can be compared;
      - Welch t-test p-value, and BH-adjusted q-value across clocks;
      - if covariates are given (e.g. sex), the case coefficient and p-value
        from y ~ case + covariates.

    This is the test that matters for a biomarker of ageing (Moqri's
    "response" criterion): does it rise in a condition known to shorten life?
    """
    g = groups.astype("string")
    rows = []
    for clock in deviations.columns:
        df = pd.concat({"dev": deviations[clock], "grp": g}, axis=1, join="inner").dropna()
        df = df[df["grp"].isin([case, control])]
        x1 = df.loc[df["grp"] == case, "dev"].to_numpy(float)
        x0 = df.loc[df["grp"] == control, "dev"].to_numpy(float)
        n1, n0 = len(x1), len(x0)
        row = {"clock": clock, "n_case": n1, "n_control": n0}
        if n1 < 2 or n0 < 2:
            rows.append(row)
            continue
        diff = x1.mean() - x0.mean()
        pooled = np.sqrt(((n1 - 1) * x1.var(ddof=1) + (n0 - 1) * x0.var(ddof=1)) / (n1 + n0 - 2))
        d = diff / pooled if pooled > 0 else np.nan
        se_d = np.sqrt((n1 + n0) / (n1 * n0) + d**2 / (2 * (n1 + n0)))
        row.update(
            mean_case=x1.mean(),
            mean_control=x0.mean(),
            diff=diff,
            cohens_d=d,
            d_ci_low=d - 1.96 * se_d,
            d_ci_high=d + 1.96 * se_d,
            p_welch=stats.ttest_ind(x1, x0, equal_var=False).pvalue,
        )
        if covariates is not None:
            cov = covariates.reindex(df.index)
            keep = cov.notna().all(axis=1).to_numpy()
            y = df["dev"].to_numpy(float)[keep]
            grp = (df["grp"] == case).to_numpy(float)[keep]
            coef, se, p = _ols_group_effect(y, grp, cov.to_numpy(float)[keep])
            row.update(diff_adjusted=coef, se_adjusted=se, p_adjusted=p)
        rows.append(row)
    out = pd.DataFrame(rows).set_index("clock")
    if "p_welch" in out:
        out["q_welch"] = bh_adjust(out["p_welch"])
    if "p_adjusted" in out:
        out["q_adjusted"] = bh_adjust(out["p_adjusted"])
    return out
