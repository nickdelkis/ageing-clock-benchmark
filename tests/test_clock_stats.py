"""Checks of the statistics on synthetic data with known answers.

Run inside the container:  docker compose run --rm clocks pytest -q
"""

import numpy as np
import pandas as pd
import pytest

from agetarget.clocks.stats import (
    age_deviation,
    bh_adjust,
    clock_metrics,
    compare_groups,
    deviation_correlations,
    deviation_table,
)


@pytest.fixture
def cohort():
    rng = np.random.default_rng(0)
    n = 200
    ids = [f"S{i}" for i in range(n)]
    age = pd.Series(rng.uniform(20, 80, n), index=ids)
    group = pd.Series(np.where(np.arange(n) < n // 2, "case", "control"), index=ids)
    accel = np.where(group == "case", 4.0, 0.0)  # cases are 4 years "older"
    # A biased clock: regresses toward the mean, plus noise and the case effect
    biased = 15 + 0.7 * age + accel + rng.normal(0, 3, n)
    exact = age + rng.normal(0, 0.01, n)
    pace = pd.Series(1.0 + 0.05 * (group == "case") + rng.normal(0, 0.05, n), index=ids)
    preds = pd.DataFrame({"biased": biased, "exact": exact, "pace": pace}, index=ids)
    return age, group, preds


def test_residual_deviation_is_uncorrelated_with_age(cohort):
    age, _, preds = cohort
    dev = age_deviation(preds["biased"], age)
    assert abs(np.corrcoef(dev, age)[0, 1]) < 1e-8
    assert abs(dev.mean()) < 1e-8


def test_raw_deviation_is_prediction_minus_age(cohort):
    age, _, preds = cohort
    raw = age_deviation(preds["exact"], age, method="raw")
    assert np.allclose(raw, preds["exact"] - age)


def test_deviation_aligns_on_sample_ids(cohort):
    age, _, preds = cohort
    shuffled = preds["biased"].sample(frac=1, random_state=1)
    assert np.allclose(age_deviation(shuffled, age).sort_index(), age_deviation(preds["biased"], age).sort_index())


def test_metrics_skip_errors_for_pace_clocks(cohort):
    age, _, preds = cohort
    m = clock_metrics(preds, age, {"biased": "age", "exact": "age", "pace": "pace"})
    assert m.loc["exact", "mae_years"] < 0.05
    assert m.loc["exact", "pearson_r"] > 0.999
    assert np.isnan(m.loc["pace", "mae_years"])


def test_case_effect_is_recovered(cohort):
    age, group, preds = cohort
    devs = deviation_table(preds[["biased"]], age)
    res = compare_groups(devs, group, case="case", control="control")
    # residualising on age keeps the group effect because groups have similar ages
    assert res.loc["biased", "diff"] == pytest.approx(4.0, abs=1.2)
    assert res.loc["biased", "cohens_d"] > 0.8
    assert res.loc["biased", "p_welch"] < 1e-6


def test_covariate_adjustment_runs_and_agrees(cohort):
    age, group, preds = cohort
    rng = np.random.default_rng(1)
    sex = pd.Series(rng.integers(0, 2, len(age)).astype(float), index=age.index)
    devs = deviation_table(preds[["biased"]], age)
    res = compare_groups(devs, group, "case", "control", covariates=sex.to_frame("sex"))
    assert res.loc["biased", "diff_adjusted"] == pytest.approx(res.loc["biased", "diff"], abs=0.5)
    assert res.loc["biased", "p_adjusted"] < 1e-6


def test_correlation_matrix_shape_and_diagonal(cohort):
    age, _, preds = cohort
    corr = deviation_correlations(deviation_table(preds, age))
    assert corr.shape == (3, 3)
    assert np.allclose(np.diag(corr), 1.0)


def test_bh_matches_hand_calculation():
    p = [0.01, 0.04, 0.03, np.nan, 0.20]
    q = bh_adjust(p)
    # sorted p: 0.01, 0.03, 0.04, 0.20 with n=4 -> 0.04, 0.0533, 0.0533, 0.20
    assert q[0] == pytest.approx(0.04)
    assert q[2] == pytest.approx(0.04 * 4 / 3)
    assert q[1] == pytest.approx(0.04 * 4 / 3)
    assert np.isnan(q[3])
    assert q[4] == pytest.approx(0.20)


def test_too_few_samples_raises():
    s = pd.Series([1.0, 2.0], index=["a", "b"])
    with pytest.raises(ValueError):
        age_deviation(s, s)


# ---- meta-analysis ------------------------------------------------------------

from agetarget.clocks.stats import meta_analyse


def test_meta_identical_studies_have_no_heterogeneity():
    m = meta_analyse([0.5, 0.5, 0.5], [0.1, 0.2, 0.3])
    assert m["q"] == pytest.approx(0) and m["tau2"] == 0 and m["i2"] == 0
    assert m["random"] == pytest.approx(0.5) and m["fixed"] == pytest.approx(0.5)


def test_meta_fixed_effect_weights_by_inverse_variance():
    m = meta_analyse([0.0, 1.0], [1.0, 1.0])
    assert m["fixed"] == pytest.approx(0.5)
    assert m["fixed_se"] == pytest.approx(np.sqrt(0.5))
    assert m["tau2"] == 0  # Q = 0.5 < df = 1


def test_meta_dersimonian_laird_worked_example():
    # w = 4 each; FE = 2; Q = 32; C = 12 - 48/12 = 8; tau2 = (32 - 2) / 8 = 3.75
    m = meta_analyse([0.0, 2.0, 4.0], [0.5, 0.5, 0.5])
    assert m["q"] == pytest.approx(32)
    assert m["tau2"] == pytest.approx(3.75)
    assert m["i2"] == pytest.approx(30 / 32)
    assert m["random"] == pytest.approx(2.0)
    assert m["random_se"] == pytest.approx(np.sqrt(1 / 0.75))
    # HKSJ: q* = sum(w*(y - mu)^2) / (k - 1) = 0.25 * 8 / 2 = 1, so se = sqrt(1 / 0.75); t(2) critical value
    half = m["hk_ci_high"] - m["random"]
    assert half == pytest.approx(4.302653 * np.sqrt(1 / 0.75), rel=1e-5)


def test_meta_skips_missing_studies():
    m = meta_analyse([1.0, np.nan, 3.0], [1.0, 1.0, np.nan])
    assert m["k"] == 1 and m["fixed"] == pytest.approx(1.0) and "random" not in m
