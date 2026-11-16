"""The scoring rubric shared by the agent and the rule-based baseline.

Each dimension is scored 1-5 (5 = most favourable for prioritisation).
The baseline turns facts into scores with fixed rules; it is deliberately crude
and exists as a reference point for the agent, not as the answer.
"""

from __future__ import annotations


DIMENSIONS = {
    "ageing_relevance": (
        "Evidence that the target is involved in human ageing or age-related disease: "
        "the share of the target's papers on ageing/senescence (raw counts mostly reflect popularity), "
        "associations with age-related diseases, and the project context. "
        "5 = strong, multi-source evidence; 1 = none."
    ),
    "mechanism": (
        "How well the target's biological function and its link to ageing are understood, and whether a "
        "modulation direction (inhibit or activate) is clear. 5 = well-characterised with a clear direction; 1 = unknown."
    ),
    "tractability": (
        "Feasibility of modulating the target with a drug modality (small molecule, antibody, PROTAC, other), "
        "from Open Targets tractability. 5 = approved-drug precedence; 1 = no tractability evidence."
    ),
    "safety": (
        "Absence of known safety liabilities for modulating the target. 5 = no known liabilities and benign biology; "
        "1 = serious, well-documented liabilities. Absence of data is not evidence of safety: cap at 4 without data."
    ),
    "clinical_precedence": (
        "Drugs acting on the target that have reached the clinic. 5 = approved drug; 4 = phase 3; 3 = phase 2; "
        "2 = phase 1; 1 = none. For secreted ligands, drugs may act on the receptor or replace the protein "
        "instead of binding the target itself; such drugs are not listed for the target."
    ),
}

WEIGHTS = {"ageing_relevance": 0.30, "mechanism": 0.15, "tractability": 0.20, "safety": 0.20, "clinical_precedence": 0.15}


def overall(scores: dict[str, float]) -> float:
    return round(sum(WEIGHTS[d] * scores[d] for d in WEIGHTS), 2)


def _bucket(n: float, cuts: list[float]) -> int:
    """1 + number of cut-points that n reaches."""
    return 1 + sum(n >= c for c in cuts)


def literature_share(f: dict) -> float:
    """Fraction of the target's papers that are about ageing or senescence (can double count overlap)."""
    return f.get("literature.ageing_share", 0.0) + f.get("literature.senescence_share", 0.0)


def baseline_scores(f: dict, lit_score: int | None = None) -> dict[str, int]:
    """Rule-based scores from flat facts (see dossier.facts).

    lit_score: 1-5 literature component. baseline_table() sets it relative to the other
    candidates, because well-studied proteins saturate any absolute threshold. Without it,
    an absolute scale on the share of ageing/senescence papers is used.
    """
    # ageing relevance: share of literature on ageing, plus age-related disease associations
    if lit_score is None:
        lit_score = _bucket(literature_share(f), [0.05, 0.10, 0.20, 0.35])
    ageing = min(5, round((lit_score + _bucket(f.get("associations.n_ageing", 0), [1, 3, 6, 10])) / 2))

    # mechanism: annotated function, measurable (secreted) protein, any age-related disease link.
    # Capped at 4: judging how well the link to ageing is understood is left to the agent.
    mechanism = 1 + bool(f.get("uniprot.function")) + bool(f.get("uniprot.secreted")) + (f.get("associations.n_ageing", 0) > 0)

    # tractability: best evidence across modalities
    labels = " | ".join(" | ".join(f.get(f"tractability.{m}", [])) for m in
                        ("small_molecule", "antibody", "protac", "other_modality")).lower()
    if "approved" in labels:
        tract = 5
    elif "clinical" in labels:
        tract = 4
    elif any(k in labels for k in ("ligand", "pocket", "structure", "druggable")):
        tract = 3
    elif labels.strip(" |"):
        tract = 2
    else:
        tract = 1

    n_liab = f.get("safety.n_liabilities", 0)
    safety = 4 if n_liab == 0 else _bucket(-n_liab, [-5, -2]) + 0  # 1-2 -> 3, 3-5 -> 2, >5 -> 1

    clinical = 1 + f.get("clinical.max_stage", 0)

    return {"ageing_relevance": ageing, "mechanism": mechanism, "tractability": tract,
            "safety": safety, "clinical_precedence": clinical}
