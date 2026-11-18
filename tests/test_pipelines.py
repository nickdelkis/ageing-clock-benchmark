"""The pipeline steps that run without Biolearn or an LLM: QC helpers, pooling, assessing a saved batch."""

import numpy as np
import pandas as pd
import pytest

from agetarget import config as cfg
from agetarget.__main__ import main
from agetarget.clocks import pipeline as clocks
from agetarget.targets import pipeline as targets


def test_unusable_ages_catches_missing_and_implausible():
    age = pd.Series([23, np.nan, 891, "NA", 57.5, -1], index=list("abcdef"))
    dropped, implausible = clocks.unusable_ages(age)
    assert sorted(dropped) == ["b", "c", "d", "f"]
    assert implausible.to_dict() == {"c": 891, "f": -1}


def test_sex_check_needs_enough_probes():
    assert clocks.sex_check_possible({"X": 0.99, "Y": 0.24})       # GSE80417: X complete, most Y missing
    assert not clocks.sex_check_possible({"X": 0.0, "Y": 0.0})     # GSE84727: no sex-chromosome probes


def test_sample_status_first_reason_wins():
    status = clocks.sample_status(pd.Index(list("abcde")), no_age=["a"], sex_mismatch=["b", "a"], manual=["c", "b"])
    assert status.to_dict() == {"a": "no usable age", "b": "sex mismatch", "c": "manual exclusion",
                                "d": "QC-passed", "e": "QC-passed"}


def test_adjusted_effects_refits_residuals_per_sample_set():
    rng = np.random.default_rng(0)
    idx = pd.Index([f"s{i}" for i in range(80)])
    age = pd.Series(rng.uniform(20, 70, 80), index=idx)
    groups = pd.Series(np.where(np.arange(80) < 40, cfg.CASE, cfg.CONTROL), index=idx, dtype="string")
    preds = pd.DataFrame({"clock": age + 3 * (groups == cfg.CASE) + rng.normal(0, 1, 80)})
    sex = pd.Series(rng.integers(0, 2, 80).astype(float), index=idx, name="sex")
    out = clocks.adjusted_effects(preds, age, groups, {"sex": [sex]}, {"all": idx, "subset": idx[:60]})
    assert set(out["samples"]) == {"all", "subset"}
    assert out.loc[out.samples == "all", "diff_adjusted"].item() == pytest.approx(3, abs=0.5)
    assert out.loc[out.samples == "subset", "n_control"].item() == 20


def test_pool_reads_each_cohort_and_writes_the_table(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CLOCK_RESULTS", tmp_path)
    rows = []
    for gse, diff in [("A", 0.10), ("B", 0.12), ("C", 0.08)]:
        df = pd.DataFrame([{"clock": c, "n_case": 50, "n_control": 50, "diff_adjusted": diff, "se_adjusted": 0.02,
                            "p_adjusted": 0.01, "samples": s, "model": m}
                           for c in ["GrimAge2", "DunedinPACE"] for s in ["all", "QC-passed"] for m in cfg.COVARIATE_MODELS])
        (tmp_path / gse).mkdir()
        df.to_csv(tmp_path / gse / "case_control_adjusted.csv", index=False)
    pooled = clocks.pool(["A", "B", "C"], log=lambda _: None)
    assert pooled.loc[("DunedinPACE", "sex"), "random"] == pytest.approx(0.10)
    assert pooled.loc[("DunedinPACE", "sex"), "n_case"] == 150
    assert {p.name for p in (tmp_path / "pooled").iterdir()} == {"pooled_effects.csv", "pooled_GrimAge2.png",
                                                                 "pooled_DunedinPACE.png"}


@pytest.mark.skipif(not (cfg.AGENT_RUNS / "20261117-094506").exists(), reason="committed batch not present")
def test_committed_batch_reproduces(tmp_path):
    """Regression guard: the saved version 3 batch must give the published citation check and ranking."""
    rank = targets.assess("20261117-094506", out=tmp_path, log=lambda _: None)
    citations = pd.read_csv(tmp_path / "citations.csv")
    assert citations.status.value_counts().to_dict() == {"match": 264, "mismatch": 1}
    assert list(rank.index[:3]) == ["SERPINE1", "ADM", "GDF15"]
    assert rank.loc["SERPINE1", "agent_overall"] == pytest.approx(3.37, abs=0.005)
    weights = pd.read_csv(tmp_path / "weight_sensitivity.csv", index_col=[0, 1])
    assert weights.loc[("near chosen weights", "SERPINE1"), "p_first"] == pytest.approx(0.888, abs=0.001)


def test_cli_rejects_unknown_step():
    with pytest.raises(SystemExit):
        main(["nonsense"])
