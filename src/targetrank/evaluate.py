"""Checks on agent assessments: are citations real, does the agent agree with the
rule-based baseline, is it stable across runs, and did it look at all the evidence?"""

from __future__ import annotations

import difflib
import json
import math
import re
import unicodedata

import pandas as pd
from scipy import stats

from . import dossier as ds
from .agent import EVIDENCE_TOOLS, AgentResult
from .rubric import DIMENSIONS, baseline_scores, literature_share, overall


def _norm(x):
    """Lower-case, unify unicode, strip UniProt reference tags such as (PubMed:123) and {ECO:...}."""
    if not isinstance(x, str):
        return x
    s = unicodedata.normalize("NFKC", x)
    s = re.sub(r"\((?:PubMed|By similarity|Ref\.)[^)]*\)", "", s, flags=re.I)
    s = re.sub(r"\{ECO:[^}]*\}", "", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([.,;:])", r"\1", s)
    return s.strip().lower()


def _parse(cited):
    """The agent sometimes passes a JSON value as a string, e.g. "[]" or "2"."""
    if isinstance(cited, str):
        t = cited.strip()
        if t[:1] in "[{" or t in ("true", "false", "null") or re.fullmatch(r"-?\d+(\.\d+)?", t):
            try:
                return json.loads(t)
            except json.JSONDecodeError:
                pass
    return cited


def _similar(fragment: str, text: str, threshold: float = 0.85) -> bool:
    """Is the fragment a close (not exact) paraphrase of some part of the text?"""
    n = len(fragment)
    if n < 15 or not text:
        return False
    step = max(1, n // 4)
    best = 0.0
    for start in range(0, max(1, len(text) - n + 1), step):
        best = max(best, difflib.SequenceMatcher(None, fragment, text[start:start + n + n // 5]).ratio())
        if best >= threshold:
            return True
    return False


def _fragments(text: str) -> list[str]:
    """Split a quote on ellipses and sentence ends, so an abridged quote (with or without "...")
    is checked piece by piece. Every piece must still appear verbatim in the source."""
    parts = [p.strip(" .,;:") for p in re.split(r"\.\.\.|\u2026|(?<=[.;])\s+", text)]
    return [p for p in parts if len(p) >= 3]


def values_match(cited, actual) -> bool:
    """Lenient but honest comparison of a cited value with the stored fact.

    Empty lists match empty lists; abridged quotes ("A ... B") match if every
    fragment appears in the stored text; numbers match within 1%.
    """
    cited = _parse(cited)
    if isinstance(actual, bool) or isinstance(cited, bool):
        return str(cited).strip().lower() == str(actual).strip().lower()
    if isinstance(actual, (int, float)):
        try:
            return math.isclose(float(cited), float(actual), rel_tol=0.01, abs_tol=1e-9)
        except (TypeError, ValueError):
            return False
    if isinstance(actual, list):
        items = cited if isinstance(cited, list) else [cited]
        if not items:
            return not actual
        pool = [_norm(str(a)) for a in actual]

        def in_pool(text) -> bool:
            t = _norm(str(text))
            if not t:
                return False
            if any(t == p or t in p for p in pool):
                return True
            frags = _fragments(t)
            return bool(frags) and any(all(f in p for f in frags) for p in pool)

        def item_ok(i) -> bool:
            if in_pool(i):
                return True
            # a list cited as one comma-separated string: check each piece
            pieces = [x for x in re.split(r",\s*|;\s*", str(i)) if len(x.strip(" .")) >= 3]
            return len(pieces) > 1 and all(in_pool(x) for x in pieces)

        return all(item_ok(i) for i in items)
    if isinstance(actual, str):
        c, a = _norm(str(cited)), _norm(actual)
        if not c:
            return False
        if c == a or c in a:
            return True
        frags = _fragments(c)
        return bool(frags) and all(f in a for f in frags)
    return cited == actual


def match_status(cited, actual) -> str:
    """'match' (exact, allowing format differences), 'approximate' (close paraphrase of a text
    fact) or 'mismatch'. Only text facts can be approximate; numbers and lists must match."""
    cited = _parse(cited)
    if values_match(cited, actual):
        return "match"
    if isinstance(actual, str) and isinstance(cited, str):
        a = _norm(actual)
        frags = _fragments(_norm(cited)) or [_norm(cited)]
        if all(f in a or _similar(f, a) for f in frags):
            return "approximate"
    return "mismatch"


def citation_check(results: list[AgentResult], dossiers: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        if not r.assessment:
            continue
        f = ds.facts(dossiers[r.target])
        for dim, s in r.assessment["scores"].items():
            for ev in s.get("evidence") or []:
                fid = ev.get("fact_id")
                if fid not in f:
                    status, actual = "unknown fact", None
                else:
                    actual = f[fid]
                    status = match_status(ev.get("value"), actual)
                rows.append({"target": r.target, "run": r.run, "dimension": dim, "fact_id": fid,
                             "cited": ev.get("value"), "actual": actual, "status": status})
    return pd.DataFrame(rows, columns=["target", "run", "dimension", "fact_id", "cited", "actual", "status"])


def scores_long(results: list[AgentResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        if not r.assessment:
            continue
        sc = {d: r.assessment["scores"][d]["score"] for d in DIMENSIONS}
        for d, v in {**sc, "overall": overall(sc)}.items():
            rows.append({"target": r.target, "run": r.run, "dimension": d, "score": v})
    return pd.DataFrame(rows, columns=["target", "run", "dimension", "score"])


def baseline_table(dossiers: dict[str, dict]) -> pd.DataFrame:
    """Baseline scores; the literature component is ranked relative to the other candidates (1-5)."""
    facts = {sym: ds.facts(d) for sym, d in dossiers.items()}
    share = pd.Series({sym: literature_share(f) for sym, f in facts.items()})
    pct = share.rank(pct=True, method="average") if len(share) > 1 else pd.Series(1.0, index=share.index)
    lo = pct.min()
    rel = {sym: 1 + round(4 * (p - lo) / (1 - lo)) if lo < 1 else 3 for sym, p in pct.items()}
    rows = {}
    for sym, f in facts.items():
        b = baseline_scores(f, lit_score=rel[sym])
        rows[sym] = {**b, "overall": overall(b)}
    out = pd.DataFrame(rows).T
    out.insert(0, "ageing_lit_share", share.round(3))
    return out


def ranking(results: list[AgentResult], dossiers: dict[str, dict]) -> pd.DataFrame:
    """Mean agent score per target (with run-to-run spread) next to the baseline."""
    long = scores_long(results)
    overall_runs = long[long.dimension == "overall"].pivot(index="target", columns="run", values="score")
    agent = long.groupby(["target", "dimension"]).score.mean().unstack()
    base = baseline_table(dossiers)
    recs = {}
    for r in results:
        if r.assessment:
            recs.setdefault(r.target, []).append(r.assessment["recommendation"])
    out = pd.DataFrame({
        "agent_overall": agent["overall"],
        "agent_min": overall_runs.min(axis=1),
        "agent_max": overall_runs.max(axis=1),
        "baseline_overall": base["overall"],
        "recommendation": {t: max(set(v), key=v.count) for t, v in recs.items()},
    })
    out["agent_rank"] = out["agent_overall"].rank(ascending=False, method="min").astype("Int64")
    out["baseline_rank"] = out["baseline_overall"].rank(ascending=False, method="min").astype("Int64")
    return out.sort_values("agent_overall", ascending=False)


def agreement(results: list[AgentResult], dossiers: dict[str, dict]) -> pd.DataFrame:
    """Spearman correlation across targets between mean agent score and baseline, per dimension."""
    agent = scores_long(results).groupby(["target", "dimension"]).score.mean().unstack()
    base = baseline_table(dossiers).loc[agent.index]
    rows = []
    for d in list(DIMENSIONS) + ["overall"]:
        a, b = agent[d].astype(float), base[d].astype(float)
        rho = stats.spearmanr(a, b).statistic if a.nunique() > 1 and b.nunique() > 1 else float("nan")
        rows.append({"dimension": d, "spearman_rho": rho, "mean_abs_diff": (a - b).abs().mean()})
    return pd.DataFrame(rows).set_index("dimension")


def run_summary(results: list[AgentResult]) -> pd.DataFrame:
    """Per run: did it finish, how many turns, which evidence tools were used."""
    rows = []
    for r in results:
        called = set(r.tools_called)
        n_bg = sum(len(s.get("background_knowledge") or []) for s in (r.assessment or {}).get("scores", {}).values())
        rows.append({"target": r.target, "run": r.run, "completed": r.assessment is not None, "turns": r.n_turns,
                     "tool_coverage": len(called & set(EVIDENCE_TOOLS)) / len(EVIDENCE_TOOLS),
                     "missed_tools": ", ".join(sorted(set(EVIDENCE_TOOLS) - called)),
                     "background_claims": n_bg,
                     "conflicts_flagged": len((r.assessment or {}).get("source_conflicts") or []),
                     "error": r.error})
    return pd.DataFrame(rows)


def turn_diagnostics(results: list[AgentResult]) -> pd.DataFrame:
    """Why did a run need extra turns? Counts rejected submissions (with reasons), nudges and repeated tool calls."""
    rows = []
    for r in results:
        rejected = [json.loads(m["content"]).get("problems", []) for m in r.trace
                    if m["role"] == "tool" and m.get("name") == "submit_assessment" and '"rejected"' in m["content"]]
        nudges = sum(1 for m in r.trace if m["role"] == "user" and m["content"].startswith("Please continue"))
        calls = [c["name"] for m in r.trace if m["role"] == "assistant" for c in m.get("tool_calls") or []]
        evidence_calls = [c for c in calls if c != "submit_assessment"]
        rows.append({"target": r.target, "run": r.run, "turns": r.n_turns, "completed": r.assessment is not None,
                     "rejected_submissions": len(rejected), "nudges": nudges,
                     "repeated_tool_calls": len(evidence_calls) - len(set(evidence_calls)),
                     "rejection_reasons": "; ".join(sorted({p for ps in rejected for p in ps}))[:300]})
    return pd.DataFrame(rows)
