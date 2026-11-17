"""The assessment agent: reads cached evidence through tools, returns a cited, structured assessment.

Design choices, for auditability:
- Tools only read the cached dossier, so every run sees identical evidence.
- The final answer is a tool call (submit_assessment) with a fixed schema, which works
  the same way across providers and is validated before it is accepted.
- Every score must cite fact_ids with their values; claims from the model's own
  knowledge go in a separate field, so evaluation can tell them apart.
- The full message trace is kept for review.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import dossier as ds
from .llm import LLMClient
from .rubric import DIMENSIONS, WEIGHTS

EVIDENCE_TOOLS = {
    "get_identity_and_function": "Gene identifiers, protein name, UniProt function summary and subcellular location.",
    "get_tractability": "Open Targets tractability evidence per drug modality (small molecule, antibody, PROTAC, other).",
    "get_safety": "Known safety liabilities for modulating the target (Open Targets).",
    "get_clinical_candidates": "Drugs acting on the target and the highest clinical stage reached (Open Targets).",
    "get_disease_associations": "Open Targets disease associations, including age-related diseases, with scores.",
    "get_literature_counts": "Europe PMC publication counts for the target overall and with ageing, senescence and schizophrenia.",
    "get_project_context": "Why this target is on the list: findings from the epigenetic-clock project.",
}

_EVIDENCE_ITEM = {
    "type": "object",
    "properties": {"fact_id": {"type": "string"}, "value": {"description": "The value exactly as returned by the tool"}},
    "required": ["fact_id", "value"],
}
_DIMENSION = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "rationale": {"type": "string", "description": "One to three sentences."},
        "evidence": {"type": "array", "items": _EVIDENCE_ITEM, "description": "Facts from the tools supporting the score."},
        "background_knowledge": {"type": "array", "items": {"type": "string"},
                                 "description": "Claims used that did NOT come from the tools."},
    },
    "required": ["score", "rationale", "evidence", "background_knowledge"],
}
SUBMIT_TOOL = {
    "name": "submit_assessment",
    "description": "Submit the final assessment. Call exactly once, after gathering evidence.",
    "parameters": {
        "type": "object",
        # Short decision fields first: if a long answer is ever cut off, these are not the ones lost
        "properties": {
            "target": {"type": "string"},
            "recommendation": {"type": "string", "enum": ["prioritise", "consider", "deprioritise"]},
            "proposed_modulation": {"type": "string", "enum": ["inhibit", "activate", "unclear"]},
            "scores": {"type": "object", "properties": {d: _DIMENSION for d in DIMENSIONS}, "required": list(DIMENSIONS)},
            "summary": {"type": "string", "description": "Three to five sentences for a review meeting; the last states the recommendation."},
            "key_uncertainties": {"type": "array", "items": {"type": "string"}},
            "source_conflicts": {"type": "array", "items": {"type": "string"},
                                 "description": "Disagreements between sources and which one you relied on. Empty if none."},
        },
        "required": ["target", "proposed_modulation", "scores", "summary", "key_uncertainties", "source_conflicts",
                     "recommendation"],
    },
}
TOOLS = [{"name": n, "description": d, "parameters": {"type": "object", "properties": {}}}
         for n, d in EVIDENCE_TOOLS.items()] + [SUBMIT_TOOL]

SYSTEM_PROMPT = """You assess candidate drug targets for a healthy-ageing research platform.

Work in two steps:
1. Gather evidence by calling the evidence tools. Each returns facts as {{fact_id: value}}.
2. Call submit_assessment once with a score of 1-5 (5 = most favourable) for each dimension.

Dimensions:
{dimensions}

Rules:
- Base scores on the tool facts. For every score, cite the supporting facts as {{"fact_id", "value"}}
  with the value copied exactly as the tool returned it.
- Every factual statement in a rationale or the summary must either come from a cited fact or be listed
  in background_knowledge. Anything the tools did not return goes in background_knowledge, never in evidence.
- Project context: apply each finding only to what it describes. A result about the GrimAge clock as a whole
  is not a result about this protein's surrogate, and a finding about the methylation surrogate is not a
  finding about the measured protein.
- Compare the sources with each other (for example tractability labels against the clinical candidates list,
  literature against disease associations). Report every disagreement in source_conflicts and say which
  source you relied on; do not silently pick one. Use an empty list if there are none.
- Say whether you would inhibit or activate the target to slow ageing, or "unclear". If unclear, name in
  key_uncertainties the evidence that would resolve it.
- Missing evidence lowers confidence; it is not evidence of safety or efficacy.
- Drugs you know of but the tools do not list may be mentioned in background_knowledge, but do not score them.
- The recommendation is exactly one of prioritise, consider or deprioritise, and the summary's last
  sentence states it in those words.
- Be concise: one to three sentences per rationale, short list items. Do not invent drugs, trials, numbers or papers."""


def system_prompt() -> str:
    dims = "\n".join(f"- {d} (weight {WEIGHTS[d]:.2f}): {text}" for d, text in DIMENSIONS.items())
    return SYSTEM_PROMPT.format(dimensions=dims)


@dataclass
class AgentResult:
    target: str
    model: str
    run: int
    assessment: dict | None
    tools_called: list[str] = field(default_factory=list)
    n_turns: int = 0
    error: str | None = None
    trace: list[dict] = field(default_factory=list, repr=False)


_SPELLING = {"prioritize": "prioritise", "deprioritize": "deprioritise"}


def normalise(assessment: dict) -> None:
    """Accept harmless variants in enum fields (case, whitespace, US spelling) instead of rejecting them."""
    for key in ("recommendation", "proposed_modulation"):
        v = assessment.get(key)
        if isinstance(v, str):
            v = v.strip().lower()
            assessment[key] = _SPELLING.get(v, v)


def validate(assessment: dict) -> list[str]:
    normalise(assessment)
    problems = []
    scores = assessment.get("scores") or {}
    for d in DIMENSIONS:
        s = scores.get(d)
        if not isinstance(s, dict):
            problems.append(f"scores.{d} is missing")
            continue
        if not isinstance(s.get("score"), int) or not 1 <= s["score"] <= 5:
            problems.append(f"scores.{d}.score must be an integer 1-5")
        if not isinstance(s.get("evidence"), list):
            problems.append(f"scores.{d}.evidence must be a list")
    if assessment.get("recommendation") not in ("prioritise", "consider", "deprioritise"):
        problems.append(f"recommendation must be prioritise, consider or deprioritise (got {assessment.get('recommendation')!r})")
    if not isinstance(assessment.get("source_conflicts", []), list):
        problems.append("source_conflicts must be a list (empty if there are none)")
    return problems


def assess(target_dossier: dict, llm: LLMClient, run: int = 0, max_turns: int = 14) -> AgentResult:
    symbol = target_dossier["symbol"]
    messages = [{"role": "user", "content": f"Assess the target {symbol}. Gather evidence with the tools, "
                                            f"then call submit_assessment."}]
    result = AgentResult(target=symbol, model=llm.describe(), run=run, assessment=None)
    nudges = 0
    for turn in range(max_turns):
        result.n_turns = turn + 1
        try:
            reply = llm.chat(system_prompt(), messages, TOOLS)
        except Exception as exc:  # network, auth, rate limit: record and stop
            result.error = f"{type(exc).__name__}: {exc}"
            break
        messages.append({"role": "assistant", "content": reply.text, "tool_calls": reply.tool_calls})

        if not reply.tool_calls:
            if nudges >= 2:
                result.error = "Model stopped without calling submit_assessment"
                break
            nudges += 1
            messages.append({"role": "user", "content": "Please continue: use the tools, then call submit_assessment."})
            continue

        submitted = None
        for call in reply.tool_calls:
            name = call["name"]
            if name == "submit_assessment":
                submitted = call
                continue
            if name in ds.TOOL_SECTIONS:
                result.tools_called.append(name)
                content = json.dumps(ds.section(target_dossier, name), default=str)
            else:
                content = json.dumps({"error": f"Unknown tool {name}"})
            messages.append({"role": "tool", "tool_call_id": call["id"], "name": name, "content": content})

        if submitted:
            problems = validate(submitted["arguments"])
            if problems and reply.truncated:
                problems.insert(0, "Your reply was cut off at the output length limit, so fields are missing. "
                                   "Resubmit with shorter rationales, summary and lists.")
            if not problems:
                result.assessment = submitted["arguments"]
                messages.append({"role": "tool", "tool_call_id": submitted["id"], "name": "submit_assessment",
                                 "content": json.dumps({"status": "accepted"})})
                break
            messages.append({"role": "tool", "tool_call_id": submitted["id"], "name": "submit_assessment",
                             "content": json.dumps({"status": "rejected", "problems": problems})})
    else:
        result.error = result.error or f"No valid assessment within {max_turns} turns"
    result.trace = messages
    return result


def save_results(results: list[AgentResult], run_dir: Path) -> None:
    """One JSON file per result, including the full message trace."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        (run_dir / f"{r.target}_run{r.run}.json").write_text(json.dumps(asdict(r), indent=1, default=str))


def load_results(run_dir: Path) -> list[AgentResult]:
    """Read results written by save_results(), e.g. to rebuild the report of an earlier run."""
    out = []
    for path in sorted(Path(run_dir).glob("*_run*.json")):
        d = json.loads(path.read_text())
        out.append(AgentResult(**{k: d.get(k) for k in AgentResult.__dataclass_fields__ if k in d}))
    return out
