"""Tests for the target-ranking demo, with all HTTP faked (no network, no API keys).

The fake responses follow the shapes of the real APIs (Open Targets GraphQL,
UniProt REST, Europe PMC REST, Anthropic Messages, OpenAI Chat Completions).
"""

import json
from urllib.parse import parse_qs, urlparse

import pytest

from targetrank import agent, dossier as ds, evaluate, http, llm, rubric, sources

OT_SEARCH = {"data": {"search": {"hits": [
    {"id": "ENSG00000000001", "name": "ADMX", "entity": "target"},
    {"id": "ENSG00000148926", "name": "ADM", "entity": "target"},
]}}}
OT_TARGET = {"data": {"target": {
    "id": "ENSG00000148926", "approvedSymbol": "ADM", "approvedName": "adrenomedullin",
    "tractability": [
        {"label": "Approved Drug", "modality": "SM", "value": False},
        {"label": "High-Quality Pocket", "modality": "SM", "value": True},
        {"label": "UniProt loc high conf", "modality": "AB", "value": True},
    ],
    "safetyLiabilities": [
        {"event": "hypotension", "eventId": "x", "datasource": "Lit", "effects": [{"direction": "Activation/Increase/Upregulation", "dosing": None}]},
    ],
    "drugAndClinicalCandidates": {"count": 2, "rows": [
        {"maxClinicalStage": "PHASE_2", "drug": {"id": "CHEMBL1", "name": "ADRECIZUMAB", "drugType": "Antibody"},
         "diseases": [{"disease": {"name": "septic shock"}}]},
        {"maxClinicalStage": "PHASE_1", "drug": {"id": "CHEMBL1", "name": "ADRECIZUMAB", "drugType": "Antibody"},
         "diseases": [{"disease": {"name": "heart failure"}}]},
    ]},
    "associatedDiseases": {"count": 3, "rows": [
        {"score": 0.61, "disease": {"id": "EFO_1", "name": "heart failure"}},
        {"score": 0.40, "disease": {"id": "EFO_2", "name": "septic shock"}},
        {"score": 0.22, "disease": {"id": "EFO_3", "name": "type 2 diabetes mellitus"}},
    ]},
}}}
UNIPROT = {"results": [{
    "primaryAccession": "P35318",
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Pro-adrenomedullin"}}},
    "comments": [
        {"commentType": "FUNCTION", "texts": [{"value": "Potent hypotensive and vasodilatator agent."}]},
        {"commentType": "SUBCELLULAR LOCATION", "subcellularLocations": [{"location": {"value": "Secreted"}}]},
    ],
}]}


def fake_transport(method, url, headers, body, timeout):
    if "opentargets" in url:
        q = json.loads(body)["query"]
        return 200, json.dumps(OT_SEARCH if "search(" in q else OT_TARGET).encode()
    if "uniprot" in url:
        return 200, json.dumps(UNIPROT).encode()
    if "europepmc" in url:
        query = parse_qs(urlparse(url).query)["query"][0]
        n = 5000 if " AND " not in query else (300 if "aging" in query else 40)
        return 200, json.dumps({"hitCount": n}).encode()
    return 404, b"not faked"


@pytest.fixture
def adm(monkeypatch, tmp_path):
    monkeypatch.setattr(http, "TRANSPORT", fake_transport)
    return ds.load_or_fetch("ADM", tmp_path, context="GrimAge DNAm surrogate")


def test_dossier_and_facts(adm):
    f = ds.facts(adm)
    assert f["identity.ensembl_id"] == "ENSG00000148926"          # exact symbol match, not ADMX
    assert f["tractability.small_molecule"] == ["High-Quality Pocket"]   # value False rows dropped
    assert f["clinical.max_stage"] == 2 and f["clinical.n_drugs"] == 1   # one drug, best stage kept
    assert f["associations.n_ageing"] == 2                         # heart failure + type 2 diabetes
    assert f["uniprot.secreted"] is True
    assert f["literature.ageing"] == 300 and f["literature.any"] == 5000


def test_cache_is_reused(adm, tmp_path, monkeypatch):
    monkeypatch.setattr(http, "TRANSPORT", lambda *a: (500, b"offline"))
    again = ds.load_or_fetch("ADM", tmp_path)
    assert again["identity"] == adm["identity"]


def test_stage_rank():
    assert sources.stage_rank("APPROVAL") == 4
    assert sources.stage_rank("PHASE_3") == 3
    assert sources.stage_rank("PHASE_1_2") == 2
    assert sources.stage_rank(None) == 0 and sources.stage_rank("PRECLINICAL") == 0


def test_baseline_scores(adm):
    b = rubric.baseline_scores(ds.facts(adm))
    assert b["clinical_precedence"] == 3      # phase 2
    assert b["tractability"] == 3             # pocket evidence, no clinical precedence label
    assert b["safety"] == 3                   # one liability
    assert all(1 <= v <= 5 for v in b.values())


def _assessment(value_for_stage=2):
    dim = lambda s, ev: {"score": s, "rationale": "r", "evidence": ev, "background_knowledge": []}
    return {
        "target": "ADM", "proposed_modulation": "inhibit", "summary": "s", "key_uncertainties": [],
        "source_conflicts": ["Tractability says advanced clinical; candidates list stops at phase 2. Used the list."],
        "recommendation": "consider",
        "scores": {
            "ageing_relevance": dim(4, [{"fact_id": "literature.ageing", "value": 300},
                                        {"fact_id": "associations.ageing", "value": ["heart failure"]}]),
            "mechanism": dim(4, [{"fact_id": "uniprot.secreted", "value": True}]),
            "tractability": dim(3, [{"fact_id": "tractability.antibody", "value": "UniProt loc high conf"}]),
            "safety": dim(3, [{"fact_id": "safety.events", "value": ["hypotension"]}]),
            "clinical_precedence": dim(3, [{"fact_id": "clinical.max_stage", "value": value_for_stage},
                                           {"fact_id": "clinical.trials", "value": 12}]),
        },
    }


class ScriptedLLM:
    """Plays back a fixed sequence of replies; records what it was sent."""
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, system, messages, tools):
        self.seen.append(list(messages))
        return self.replies.pop(0)

    def describe(self):
        return "scripted"


def test_agent_loop_rejects_then_accepts(adm):
    bad = _assessment()
    bad["scores"]["safety"]["score"] = 9
    script = ScriptedLLM([
        llm.Reply("", [{"id": "1", "name": "get_clinical_candidates", "arguments": {}},
                       {"id": "2", "name": "get_literature_counts", "arguments": {}}]),
        llm.Reply("Done.", []),                                            # stops early -> nudged
        llm.Reply("", [{"id": "3", "name": "submit_assessment", "arguments": bad}]),
        llm.Reply("", [{"id": "4", "name": "submit_assessment", "arguments": _assessment()}]),
    ])
    res = agent.assess(adm, script)
    assert res.assessment is not None and res.error is None
    assert res.tools_called == ["get_clinical_candidates", "get_literature_counts"]
    rejected = [m for m in res.trace if m["role"] == "tool" and "rejected" in m["content"]]
    assert rejected and "safety.score" in rejected[0]["content"]
    tool_msg = next(m for m in script.seen[1] if m["role"] == "tool")
    assert json.loads(tool_msg["content"])["clinical.max_stage"] == 2   # tools read the cached dossier


def test_citation_check(adm):
    ok = agent.AgentResult("ADM", "m", 0, _assessment(value_for_stage=2))
    wrong = agent.AgentResult("ADM", "m", 1, _assessment(value_for_stage=4))
    cc = evaluate.citation_check([ok, wrong], {"ADM": adm})
    run0 = cc[cc.run == 0].set_index("fact_id").status
    assert run0["clinical.max_stage"] == "match"
    assert run0["associations.ageing"] == "match"             # substring of "heart failure (0.61)"
    assert run0["clinical.trials"] == "unknown fact"          # invented fact id
    assert cc[(cc.run == 1) & (cc.fact_id == "clinical.max_stage")].status.item() == "mismatch"


def test_ranking_and_summary(adm):
    results = [agent.AgentResult("ADM", "m", i, _assessment(), tools_called=["get_safety"]) for i in range(2)]
    rk = evaluate.ranking(results, {"ADM": adm})
    assert rk.loc["ADM", "agent_overall"] == rubric.overall({d: _assessment()["scores"][d]["score"] for d in rubric.DIMENSIONS})
    rs = evaluate.run_summary(results)
    assert rs.tool_coverage.iloc[0] == pytest.approx(1 / 7)


def _capture(response):
    sent = {}
    def transport(method, url, headers, body, timeout):
        sent.update(url=url, headers=headers, body=json.loads(body))
        return 200, json.dumps(response).encode()
    return sent, transport


CONVERSATION = [
    {"role": "user", "content": "Assess ADM"},
    {"role": "assistant", "content": "", "tool_calls": [{"id": "t1", "name": "get_safety", "arguments": {}},
                                                       {"id": "t2", "name": "get_tractability", "arguments": {}}]},
    {"role": "tool", "tool_call_id": "t1", "name": "get_safety", "content": "{}"},
    {"role": "tool", "tool_call_id": "t2", "name": "get_tractability", "content": "{}"},
]


def test_anthropic_wire_format(monkeypatch):
    sent, transport = _capture({"content": [{"type": "text", "text": "ok"},
                                            {"type": "tool_use", "id": "t3", "name": "get_safety", "input": {}}]})
    monkeypatch.setattr(http, "TRANSPORT", transport)
    client = llm.LLMClient("anthropic", "claude-x", "https://api.anthropic.com", api_key="k")
    reply = client.chat("sys", CONVERSATION, agent.TOOLS)
    assert sent["url"].endswith("/v1/messages") and sent["headers"]["x-api-key"] == "k"
    msgs = sent["body"]["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]       # both tool results in one turn
    assert [b["tool_use_id"] for b in msgs[2]["content"]] == ["t1", "t2"]
    assert sent["body"]["tools"][0]["input_schema"]["type"] == "object"
    assert "temperature" not in sent["body"]                               # newer models reject it
    assert reply.text == "ok" and reply.tool_calls[0]["name"] == "get_safety"


def test_openai_wire_format(monkeypatch):
    sent, transport = _capture({"choices": [{"message": {"content": None, "tool_calls": [
        {"function": {"name": "get_tractability", "arguments": "{}"}}]}}]})   # no id, as some local servers do
    monkeypatch.setattr(http, "TRANSPORT", transport)
    client = llm.LLMClient("openai", "local-model", "http://host.docker.internal:11434/v1")
    reply = client.chat("sys", CONVERSATION, agent.TOOLS)
    assert sent["url"] == "http://host.docker.internal:11434/v1/chat/completions"
    assert "Authorization" not in sent["headers"]
    msgs = sent["body"]["messages"]
    assert msgs[0]["role"] == "system" and msgs[2]["tool_calls"][1]["function"]["name"] == "get_tractability"
    assert [m["role"] for m in msgs[3:]] == ["tool", "tool"]
    assert reply.tool_calls[0]["id"].startswith("call_") and reply.tool_calls[0]["arguments"] == {}


def test_from_env(monkeypatch):
    for v in ("LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(ValueError):
        llm.from_env()                                              # anthropic without a key
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "qwen")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    assert llm.from_env().api_key is None                           # local server needs no key


def test_curated_aliases_and_relative_baseline(monkeypatch, tmp_path):
    seen = []
    def transport(method, url, headers, body, timeout):
        if "europepmc" in url:
            seen.append(parse_qs(urlparse(url).query)["query"][0])
        return fake_transport(method, url, headers, body, timeout)
    monkeypatch.setattr(http, "TRANSPORT", transport)
    d1 = ds.load_or_fetch("ADM", tmp_path, aliases=["adrenomedullin", "MR-proADM"])
    assert seen[0] == '("adrenomedullin" OR "MR-proADM")'            # symbol not searched
    f = ds.facts(d1)
    assert f["literature.ageing_share"] == round(300 / 5000, 4)
    n_before = len(seen)
    ds.load_or_fetch("ADM", tmp_path, aliases=["adrenomedullin", "MR-proADM"])
    assert len(seen) == n_before                                     # cache reused when terms unchanged
    ds.load_or_fetch("ADM", tmp_path, aliases=["adrenomedullin"])
    assert len(seen) > n_before                                      # literature re-queried when terms change

    d2 = json.loads(json.dumps(d1)); d2["symbol"] = "X"
    d2["literature"]["counts"]["ageing"] = 2000                      # far higher ageing share
    tbl = evaluate.baseline_table({"ADM": d1, "X": d2})
    assert tbl.loc["X", "ageing_lit_share"] > tbl.loc["ADM", "ageing_lit_share"]
    assert tbl.loc["X", "ageing_relevance"] > tbl.loc["ADM", "ageing_relevance"]
    assert tbl["mechanism"].max() <= 4


def test_values_match_edge_cases():
    long = "As an inhibitor of cysteine proteinases, this protein is thought to serve an important role."
    assert evaluate.values_match([], [])                                    # empty list cited as empty
    assert not evaluate.values_match([], ["x"])
    assert evaluate.values_match("inhibitor of cysteine proteinases ... important role", long)   # abridged quote
    assert evaluate.values_match("inhibitor of cysteine proteinases… serve an important", long)
    assert not evaluate.values_match("inhibitor of serine proteases ... important role", long)   # altered quote
    assert evaluate.values_match(2, 2.0) and not evaluate.values_match(3, 2)


def test_values_match_list_cited_as_string():
    labels = ["Structure with Ligand", "High-Quality Pocket"]
    assert evaluate.values_match("Structure with Ligand, High-Quality Pocket", labels)
    assert not evaluate.values_match("Structure with Ligand, Approved Drug", labels)    # one invented item
    diseases = ["congenital plasminogen activator inhibitor type 1 deficiency (0.684)", "venous thrombosis (0.5)",
                "Abnormality of coagulation (0.3)"]
    assert evaluate.values_match("congenital plasminogen activator inhibitor type 1 deficiency (0.684), Abnorm...", diseases)


def test_report_lists_conflicts_and_prompt_rules(adm, tmp_path):
    from targetrank import report
    results = [agent.AgentResult("ADM", "m", 0, _assessment())]
    cc = evaluate.citation_check(results, {"ADM": adm})
    path = report.write_report(tmp_path / "r.md", evaluate.ranking(results, {"ADM": adm}), results, cc, model="m")
    text = path.read_text()
    assert "Conflicts between sources" in text and "Used the list." in text
    assert evaluate.run_summary(results).conflicts_flagged.item() == 1
    prompt = agent.system_prompt()
    assert "source_conflicts" in prompt and "GrimAge clock as a whole" in prompt
    assert "source_conflicts" in agent.SUBMIT_TOOL["parameters"]["required"]


def test_match_status_formats_and_paraphrase():
    fn = ("Hormone produced in response to various stresses (PubMed:123). Required for tissue tolerance in "
          "response to myocardial infarction by acting as a cardioprotective cytokine (PubMed:456, PubMed:789).")
    assert evaluate.match_status("[]", []) == "match"                          # JSON passed as a string
    assert evaluate.match_status("2", 2) == "match"
    assert evaluate.match_status("Required for tissue tolerance in response to myocardial infarction by acting", fn) == "match"
    assert evaluate.match_status("Hormone produced in response to various stresses. Required for tissue tolerance", fn) == "match"
    para = "Required for tissue tolerance after myocardial infarction, acting as a cardioprotective cytokine"
    assert evaluate.match_status(para, fn) == "approximate"
    assert evaluate.match_status("Promotes tumour growth by activating angiogenesis in the liver", fn) == "mismatch"
    assert evaluate.match_status(3, 2) == "mismatch"                            # numbers are never approximate


def test_turn_diagnostics(adm):
    bad = _assessment(); bad["scores"]["safety"]["score"] = 9
    script = ScriptedLLM([
        llm.Reply("", [{"id": "1", "name": "get_safety", "arguments": {}}]),
        llm.Reply("", [{"id": "2", "name": "get_safety", "arguments": {}}]),          # repeated call
        llm.Reply("", [{"id": "3", "name": "submit_assessment", "arguments": bad}]),  # rejected
        llm.Reply("", [{"id": "4", "name": "submit_assessment", "arguments": _assessment()}]),
    ])
    diag = evaluate.turn_diagnostics([agent.assess(adm, script)]).iloc[0]
    assert diag.rejected_submissions == 1 and diag.repeated_tool_calls == 1
    assert "safety.score" in diag.rejection_reasons


def test_truncated_reply_is_explained_to_the_model(adm):
    cut = _assessment(); del cut["recommendation"]
    script = ScriptedLLM([
        llm.Reply("", [{"id": "1", "name": "submit_assessment", "arguments": cut}], stop_reason="max_tokens"),
        llm.Reply("", [{"id": "2", "name": "submit_assessment", "arguments": _assessment()}]),
    ])
    res = agent.assess(adm, script)
    assert res.assessment is not None
    rejection = next(m["content"] for m in res.trace if m["role"] == "tool" and "rejected" in m["content"])
    assert "cut off" in rejection and "got None" in rejection
    props = list(agent.SUBMIT_TOOL["parameters"]["properties"])
    assert props.index("recommendation") < props.index("scores")       # decision fields come first


def test_stop_reason_parsed(monkeypatch):
    sent, transport = _capture({"content": [{"type": "text", "text": "x"}], "stop_reason": "max_tokens"})
    monkeypatch.setattr(http, "TRANSPORT", transport)
    reply = llm.LLMClient("anthropic", "m", "https://api.anthropic.com", api_key="k").chat("s", CONVERSATION, agent.TOOLS)
    assert reply.truncated and sent["body"]["max_tokens"] == 8192


def test_enum_variants_are_normalised():
    a = _assessment(); a["recommendation"] = " Prioritize "; a["proposed_modulation"] = "Inhibit"
    assert agent.validate(a) == [] and a["recommendation"] == "prioritise" and a["proposed_modulation"] == "inhibit"


def test_skipped_sentence_without_ellipsis_still_matches():
    src = ("Metalloproteinase inhibitor that forms complexes with metalloproteinases. Acts on MMP1 and MMP2. "
           "Also functions as a growth factor via CD63 and ITGB1. Plays a role in integrin signaling.")
    assert evaluate.match_status("Metalloproteinase inhibitor that forms complexes with metalloproteinases. "
                                 "Also functions as a growth factor via CD63 and ITGB1.", src) == "match"
    assert evaluate.match_status("Metalloproteinase inhibitor that forms complexes with metalloproteinases. "
                                 "Also functions as a growth factor via TNF receptors.", src) != "match"
