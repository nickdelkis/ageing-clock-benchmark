"""Per-target evidence dossiers: fetched once, cached as JSON, exposed as flat facts.

A fact is a (fact_id, value) pair such as ("clinical.max_stage", 4). The agent
reads facts through tools and must cite fact_ids; checks.py checks the cited
values against this cache, so every claim in an assessment is traceable.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import causal, sources

LITERATURE_TOPICS = {
    "ageing": "aging OR ageing OR longevity OR lifespan",
    "senescence": "senescence OR senescent OR SASP",
    "schizophrenia": "schizophrenia OR psychosis",
}

STAGE_LABEL = {0: "none", 1: "phase 1", 2: "phase 2", 3: "phase 3", 4: "approved"}


def _literature(symbol: str, protein_name: str | None, aliases: list[str] | None) -> dict:
    # Curated aliases avoid ambiguous symbols (e.g. "ADM", "LEP") inflating the counts
    terms = aliases or [symbol] + ([protein_name] if protein_name else [])
    return {**sources.literature_counts(terms, LITERATURE_TOPICS), "terms": terms}


def fetch_dossier(symbol: str, context: str = "", aliases: list[str] | None = None) -> dict:
    """Call every source for one gene symbol. Raises on network or API errors."""
    ident = sources.resolve_target(symbol)
    ot = sources.opentargets_profile(ident["ensembl_id"])
    uni = sources.uniprot_summary(symbol)
    return {
        "symbol": symbol,
        "retrieved": date.today().isoformat(),
        "identity": {**ident, "approved_name": ot["name"]},
        "opentargets": ot,
        "uniprot": uni,
        "literature": _literature(symbol, uni.get("protein_name"), aliases),
        "context": context,
    }


def load_or_fetch(symbol: str, cache_dir: Path, context: str = "", aliases: list[str] | None = None,
                  refresh: bool = False) -> dict:
    """Use the cached dossier if present. Literature is re-queried if the search terms changed."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{symbol}.json"
    if path.exists() and not refresh:
        dossier = json.loads(path.read_text())
        dossier["context"] = context or dossier.get("context", "")
        if aliases and dossier["literature"].get("terms") != aliases:
            dossier["literature"] = _literature(symbol, dossier["uniprot"].get("protein_name"), aliases)
            path.write_text(json.dumps(dossier, indent=1))
        return dossier
    dossier = fetch_dossier(symbol, context, aliases)
    path.write_text(json.dumps(dossier, indent=1))
    return dossier


def facts(dossier: dict) -> dict:
    """Flatten a dossier into citable facts."""
    ot, uni, lit = dossier["opentargets"], dossier["uniprot"], dossier["literature"]["counts"]
    out = {
        "identity.symbol": dossier["symbol"],
        "identity.ensembl_id": dossier["identity"]["ensembl_id"],
        "identity.approved_name": dossier["identity"].get("approved_name"),
        "uniprot.protein_name": uni.get("protein_name"),
        "uniprot.function": uni.get("function"),
        "uniprot.locations": uni.get("locations") or [],
        "uniprot.secreted": any("secreted" in loc.lower() or "extracellular" in loc.lower()
                                for loc in uni.get("locations") or []),
        "safety.n_liabilities": len(ot["safety_liabilities"]),
        "safety.events": sorted({l["event"] for l in ot["safety_liabilities"]}),
        "clinical.max_stage": ot["max_clinical_stage"],
        # label from the source string, so e.g. PHASE_2_3 is not shown as "phase 3"
        "clinical.max_stage_label": (ot["clinical_candidates"][0]["max_stage"] or STAGE_LABEL[ot["max_clinical_stage"]])
                                    if ot["clinical_candidates"] else "none",
        "clinical.n_drugs": len(ot["clinical_candidates"]),
        "clinical.drugs": [f"{d['drug']} ({d['max_stage'] or 'stage unknown'})" for d in ot["clinical_candidates"][:10]],
        "associations.n_ageing": len(ot["ageing_disease_associations"]),
        "associations.ageing": [f"{a['disease']} ({a['score']})" for a in ot["ageing_disease_associations"][:15]],
        "associations.top": [f"{a['disease']} ({a['score']})" for a in ot["top_disease_associations"]],
        "context.project": dossier.get("context") or "",
    }
    for modality in ("small_molecule", "antibody", "protac", "other_modality"):
        out[f"tractability.{modality}"] = ot["tractability"].get(modality, [])
    for key, n in lit.items():
        out[f"literature.{key}"] = n
    for key in LITERATURE_TOPICS:   # share of the target's literature on each topic: relevance, not popularity
        out[f"literature.{key}_share"] = round(lit.get(key, 0) / lit["any"], 4) if lit.get("any") else 0.0
    out["literature.search_terms"] = dossier["literature"].get("terms", [])
    # Mendelian randomisation results (mr/), attached in memory by causal.attach()
    out.update(dossier.get("causal") or causal.NOT_PROVIDED)
    return out


# Which facts each agent tool returns
TOOL_SECTIONS = {
    "get_identity_and_function": ("identity.", "uniprot."),
    "get_tractability": ("tractability.",),
    "get_safety": ("safety.",),
    "get_clinical_candidates": ("clinical.",),
    "get_disease_associations": ("associations.",),
    "get_literature_counts": ("literature.",),
    "get_project_context": ("context.",),
    "get_causal_evidence": ("causal.",),
}


def section(dossier: dict, tool_name: str) -> dict:
    prefixes = TOOL_SECTIONS[tool_name]
    return {k: v for k, v in facts(dossier).items() if k.startswith(prefixes)}
