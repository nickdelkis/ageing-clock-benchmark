"""Tests for reading the part 3 (Mendelian randomisation) results into agent facts.

The fixture CSVs follow the columns the R scripts in mr/ write, with the SERPINE1 pilot numbers.
"""

import json

import pandas as pd
import pytest

from agetarget.targets import agent, causal, checks, evidence, llm


@pytest.fixture
def mr_dir(tmp_path):
    pd.DataFrame([
        {"protein": "SERPINE1", "exposure_id": "ebi-a-GCST90019422", "study": "Pietzner 2020 (ebi-a-GCST90019422, n = 10,708)",
         "n_genome_wide": 6, "n_cis": 1},
        {"protein": "B2M", "exposure_id": "prot-c-3485_28_2", "study": "Suhre 2017 (prot-c-3485_28_2, n = 1,000)",
         "n_genome_wide": 2, "n_cis": 0},
        {"protein": "LEP", "exposure_id": None, "study": None, "n_genome_wide": 0, "n_cis": 0},
    ]).to_csv(tmp_path / "mr_exposures.csv", index=False)
    pd.DataFrame([{"SNP": "rs2227631", "exposure": "SERPINE1", "effect_allele.exposure": "A",
                   "other_allele.exposure": "G", "beta.exposure": 0.103, "se.exposure": 0.0132, "F_stat": 61.2}]
                 ).to_csv(tmp_path / "mr_instruments.csv", index=False)
    rows = []
    for outcome, b, se, p in [("parental_longevity", 0.070, 0.0221, 0.0015), ("frailty", 0.01, 0.03, 0.74),
                              ("grimage_accel_a", -0.2, 0.5, 0.69)]:
        rows.append({"id.exposure": "x", "id.outcome": "y", "outcome": outcome, "exposure": "SERPINE1",
                     "method": "Wald ratio", "nsnp": 1, "b": b, "se": se, "pval": p, "protein": "SERPINE1",
                     "harmful_sign": 1, "primary": "TRUE", "p_bonferroni": min(1, p * 20),
                     "direction": "higher protein -> worse ageing (hypothesis: inhibit)" if b > 0
                     else "higher protein -> better ageing (hypothesis: activate)"})
    pd.DataFrame(rows).to_csv(tmp_path / "mr_results.csv", index=False)
    pd.DataFrame([
        {"protein": "SERPINE1", "outcome": "parental_longevity", "exposure_id": "ebi-a-GCST90019422",
         "outcome_id": "ebi-a-GCST006697", "region": "7:100520370-101032547", "flank_kb": 250, "nsnps": 2290,
         "PP.H0.abf": 0.0, "PP.H1.abf": 0.832, "PP.H2.abf": 0.0, "PP.H3.abf": 0.0357, "PP.H4.abf": 0.132,
         "top_snp": "rs2227631", "top_snp_pp_h4": 0.939, "outcome_top_snp": "rs4268055", "outcome_top_kb": -69.2,
         "outcome_min_p": 6.3e-4, "exposure_top_snp": "rs2227631"}
    ]).to_csv(tmp_path / "coloc_SERPINE1_parental_longevity.csv", index=False)
    pd.DataFrame([
        {"study": "pietzner2020_somascan", "id": "ebi-a-GCST90019422", "rsid": "rs2227631", "ea": "G", "nea": "A", "beta": -0.064, "p": 1e-6,
         "protein": "SERPINE1", "measure": "protein"},
        {"study": "sun2018_somascan", "id": "d", "rsid": "rs2227631", "ea": "G", "nea": "A", "beta": -0.0363, "p": 0.148,
         "protein": "SERPINE1", "measure": "protein"},
        {"study": "sun2018_somascan", "id": "d", "rsid": "rs2227631", "ea": "G", "nea": "A", "beta": -0.02, "p": 0.4,
         "protein": "SERPINE1", "measure": "protein"},                     # duplicate row for a variant
        {"study": "gilly2020", "id": "b", "rsid": "rs2227631", "ea": "A", "nea": "G", "beta": 0.10, "p": 0.012,
         "protein": "SERPINE1", "measure": "protein"},                     # coded on the other allele
        {"study": "dnam_pai1_mccartney", "id": "c", "rsid": "rs2227631", "ea": "G", "nea": "A", "beta": 0.056, "p": 0.45,
         "protein": "SERPINE1", "measure": "DNAm surrogate"},
    ]).to_csv(tmp_path / "replication_rs2227631.csv", index=False)
    pd.DataFrame([
        {"id": "eqtl-a-ENSG00000106366", "trait": "ENSG00000106366", "beta": -0.3, "p": 1e-40},
        {"id": "prot-a-2902", "trait": "Tissue-type plasminogen activator", "beta": -0.1, "p": 1e-9},
        {"id": "ukb-b-1", "trait": "Pulse rate", "beta": 0.01, "p": 2e-6},
    ]).to_csv(tmp_path / "phewas_rs2227631.csv", index=False)
    return tmp_path


def test_load_serpine1(mr_dir):
    f = causal.load(mr_dir)["SERPINE1"]
    assert f["causal.mr_status"] == "tested: 1 cis instrument(s)"
    assert f["causal.instruments"] == ["rs2227631 (F = 61)"]
    assert f["causal.mr_significant_outcomes"] == ["parental_longevity"]
    assert f["causal.mr_direction"] == "higher protein -> worse ageing (hypothesis: inhibit)"
    assert f["causal.mr_n_tests_corrected"] == 3
    assert f["causal.mr_results"][0].startswith("parental_longevity: Wald ratio, 1 variant(s), b = +0.070")
    assert f["causal.mr_results"][0].endswith("Bonferroni p = 0.03; higher protein -> worse ageing (hypothesis: inhibit)")
    assert f["causal.mr_results"][1].endswith("higher protein -> better ageing (point estimate only, not significant)")
    assert f["causal.outcome_coding"][0] == "parental_longevity: positive b means worse ageing"
    coloc = f["causal.colocalisation"][0]
    assert "PP.H4 = 0.13" in coloc and "PP.H3 = 0.04" in coloc and "rs4268055, -69 kb" in coloc


def test_replication_is_on_one_allele_and_deduplicated(mr_dir):
    rep = causal.load(mr_dir)["SERPINE1"]["causal.replication"]
    assert not any(r.startswith("pietzner") for r in rep)                     # the exposure dataset is not a replication
    assert len(rep) == 3                                                      # Sun duplicate dropped
    assert "sun2018_somascan: rs2227631 allele A beta = +0.036, p = 0.15" in rep   # strongest row kept, on allele A
    assert any(r.startswith("gilly2020: rs2227631 allele A beta = +0.100") for r in rep)   # already on allele A
    assert any(r.startswith("dnam_pai1_mccartney (DNA-methylation surrogate") and "beta = -0.056" in r for r in rep)


def test_phewas_summary(mr_dir):
    f = causal.load(mr_dir)["SERPINE1"]
    assert f["causal.phewas_counts"].startswith("3 associations at p < 1e-5, of which 1 are")
    assert f["causal.phewas_top_traits"][0] == "Tissue-type plasminogen activator (p = 1.0e-09)"


def test_untested_targets_are_not_nulls(mr_dir):
    loaded = causal.load(mr_dir)
    assert loaded["B2M"]["causal.mr_status"].startswith("not tested: no cis instruments")
    assert "not a null result" in loaded["B2M"]["causal.mr_status"]
    assert loaded["LEP"]["causal.mr_status"] == "not tested: no pQTL dataset chosen"
    assert causal.load(mr_dir / "missing") == {}


def test_tool_returns_causal_facts_and_citations_check(mr_dir, monkeypatch, tmp_path):
    from test_targets import ScriptedLLM, _assessment, fake_transport
    from agetarget.targets import http
    monkeypatch.setattr(http, "TRANSPORT", fake_transport)
    adm = evidence.load_or_fetch("ADM", tmp_path / "ev", context="x")
    dossiers = {"ADM": adm}
    causal.attach(dossiers, mr_dir)
    assert evidence.section(adm, "get_causal_evidence") == causal.NOT_PROVIDED      # no MR row for ADM in the fixture

    adm["causal"] = causal.load(mr_dir)["SERPINE1"]                           # pretend, to test the round trip
    a = _assessment()
    a["scores"]["mechanism"]["evidence"] = [{"fact_id": "causal.mr_direction",
                                             "value": "higher protein -> worse ageing (hypothesis: inhibit)"}]
    script = ScriptedLLM([llm.Reply("", [{"id": "1", "name": "get_causal_evidence", "arguments": {}}]),
                          llm.Reply("", [{"id": "2", "name": "submit_assessment", "arguments": a}])])
    r = agent.assess(adm, script)
    assert r.tools_called == ["get_causal_evidence"]
    shown = json.loads(next(m for m in script.seen[1] if m["role"] == "tool")["content"])
    assert shown["causal.mr_significant_outcomes"] == ["parental_longevity"]
    cc = checks.citation_check([r], dossiers).set_index("fact_id")
    assert cc.loc["causal.mr_direction", "status"] == "match"


def test_cached_dossier_json_is_not_changed_by_attach(mr_dir, monkeypatch, tmp_path):
    from test_targets import fake_transport
    from agetarget.targets import http
    monkeypatch.setattr(http, "TRANSPORT", fake_transport)
    d = evidence.load_or_fetch("ADM", tmp_path / "ev", context="x")
    causal.attach({"ADM": d}, mr_dir)
    assert "causal" not in json.loads((tmp_path / "ev" / "ADM.json").read_text())
