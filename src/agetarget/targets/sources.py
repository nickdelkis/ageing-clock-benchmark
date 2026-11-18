"""Deterministic evidence from public APIs: Open Targets, UniProt, Europe PMC.

Each function returns a small, JSON-serialisable dict. Field names follow the
Open Targets Platform v4 GraphQL schema as of late 2026 (drug evidence lives in
`drugAndClinicalCandidates`; the older `knownDrugs` field no longer exists).
"""

from __future__ import annotations

import re
import urllib.parse

from .http import HTTPFailure, get_json, post_json

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/search"
EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ENSEMBL_LOOKUP = "https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?content-type=application/json"

# Diseases treated as "age-related" when scanning Open Targets associations
AGEING_DISEASE_TERMS = [
    "aging", "ageing", "longevity", "frailty", "sarcopenia", "osteoporosis",
    "alzheimer", "dementia", "cognitive decline", "parkinson",
    "coronary", "cardiovascular", "heart failure", "atherosclerosis", "hypertension", "stroke",
    "type 2 diabetes", "chronic kidney", "kidney failure", "macular degeneration",
    "copd", "chronic obstructive", "idiopathic pulmonary fibrosis",
]


def _ot(query: str, variables: dict) -> dict:
    out = post_json(OT_URL, {"query": query, "variables": variables})
    if out.get("errors"):
        raise HTTPFailure(f"Open Targets GraphQL error: {out['errors'][0].get('message')}")
    return out["data"]


# ---- identity ---------------------------------------------------------------

_SEARCH_Q = """
query search($q: String!) {
  search(queryString: $q, entityNames: ["target"], page: {index: 0, size: 10}) {
    hits { id name entity }
  }
}"""


def resolve_target(symbol: str) -> dict:
    """Gene symbol -> Ensembl gene ID, via Open Targets search, falling back to Ensembl REST."""
    try:
        hits = _ot(_SEARCH_Q, {"q": symbol})["search"]["hits"]
        exact = [h for h in hits if h["entity"] == "target" and h["name"].upper() == symbol.upper()]
        if exact:
            return {"symbol": symbol, "ensembl_id": exact[0]["id"], "resolved_by": "opentargets.search"}
    except (HTTPFailure, KeyError, TypeError):
        pass
    hit = get_json(ENSEMBL_LOOKUP.format(symbol=urllib.parse.quote(symbol)))
    return {"symbol": symbol, "ensembl_id": hit["id"], "resolved_by": "ensembl.lookup"}


# ---- Open Targets target profile -------------------------------------------

_TARGET_Q = """
query target($id: String!) {
  target(ensemblId: $id) {
    id
    approvedSymbol
    approvedName
    tractability { label modality value }
    safetyLiabilities { event eventId datasource effects { direction dosing } }
    drugAndClinicalCandidates {
      count
      rows { maxClinicalStage drug { id name drugType } diseases { disease { name } } }
    }
    associatedDiseases(page: {index: 0, size: 100}) {
      count
      rows { score disease { id name } }
    }
  }
}"""

_MODALITY = {"SM": "small_molecule", "AB": "antibody", "PR": "protac", "OC": "other_modality"}


def stage_rank(stage: str | None) -> int:
    """Map a clinical stage string to 0 (none) .. 4 (approved). Tolerant of wording."""
    if not stage:
        return 0
    s = stage.upper()
    if "APPROV" in s:
        return 4
    digits = [int(d) for d in re.findall(r"[1-4]", s)]
    if "PHASE" in s and digits:
        return min(max(digits), 3)
    return 0


def opentargets_profile(ensembl_id: str) -> dict:
    t = _ot(_TARGET_Q, {"id": ensembl_id})["target"]
    if t is None:
        raise HTTPFailure(f"Open Targets has no target {ensembl_id}")

    tract = {}
    for row in t.get("tractability") or []:
        if row.get("value"):
            tract.setdefault(_MODALITY.get(row["modality"], row["modality"]), []).append(row["label"])

    liabilities = []
    for row in t.get("safetyLiabilities") or []:
        liabilities.append({
            "event": row.get("event") or "unspecified",
            "datasource": row.get("datasource"),
            "directions": sorted({e["direction"] for e in (row.get("effects") or []) if e.get("direction")}),
        })

    drugs = {}
    cand = t.get("drugAndClinicalCandidates") or {"rows": []}
    for row in cand.get("rows") or []:
        drug = row.get("drug") or {}
        name = drug.get("name") or drug.get("id") or "unknown"
        entry = drugs.setdefault(name, {"drug": name, "type": drug.get("drugType"), "max_stage": row.get("maxClinicalStage"),
                                        "indications": set()})
        if stage_rank(row.get("maxClinicalStage")) > stage_rank(entry["max_stage"]):
            entry["max_stage"] = row.get("maxClinicalStage")
        for d in row.get("diseases") or []:
            if d.get("disease"):
                entry["indications"].add(d["disease"]["name"])
    drug_list = sorted(({**d, "indications": sorted(d["indications"])[:5]} for d in drugs.values()),
                       key=lambda d: -stage_rank(d["max_stage"]))

    assoc_rows = (t.get("associatedDiseases") or {}).get("rows") or []
    ageing = [{"disease": r["disease"]["name"], "score": round(r["score"], 3)}
              for r in assoc_rows if any(k in r["disease"]["name"].lower() for k in AGEING_DISEASE_TERMS)]
    top = [{"disease": r["disease"]["name"], "score": round(r["score"], 3)} for r in assoc_rows[:10]]

    return {
        "symbol": t["approvedSymbol"],
        "name": t.get("approvedName"),
        "tractability": tract,
        "safety_liabilities": liabilities,
        "clinical_candidates": drug_list,
        "max_clinical_stage": max((stage_rank(d["max_stage"]) for d in drug_list), default=0),
        "ageing_disease_associations": ageing,
        "top_disease_associations": top,
    }


# ---- UniProt -------------------------------------------------------------------

def uniprot_summary(symbol: str) -> dict:
    query = f"(gene_exact:{symbol}) AND (organism_id:9606) AND (reviewed:true)"
    url = UNIPROT_URL + "?" + urllib.parse.urlencode({
        "query": query, "format": "json", "size": 1,
        "fields": "accession,protein_name,cc_function,cc_subcellular_location",
    })
    results = get_json(url).get("results") or []
    if not results:
        return {"accession": None, "protein_name": None, "function": None, "locations": []}
    r = results[0]
    name = (((r.get("proteinDescription") or {}).get("recommendedName") or {}).get("fullName") or {}).get("value")
    function, locations = None, []
    for c in r.get("comments") or []:
        if c.get("commentType") == "FUNCTION" and c.get("texts"):
            function = " ".join(t["value"] for t in c["texts"])
        if c.get("commentType") == "SUBCELLULAR LOCATION":
            for loc in c.get("subcellularLocations") or []:
                value = (loc.get("location") or {}).get("value")
                if value and value not in locations:
                    locations.append(value)
    return {"accession": r.get("primaryAccession"), "protein_name": name, "function": function, "locations": locations}


# ---- Europe PMC ----------------------------------------------------------------

def europepmc_count(query: str) -> int:
    url = EUROPEPMC_URL + "?" + urllib.parse.urlencode({"query": query, "format": "json", "pageSize": 1})
    return int(get_json(url).get("hitCount", 0))


def literature_counts(terms: list[str], topics: dict[str, str]) -> dict:
    """Europe PMC hit counts for the target's names alone and combined with each topic."""
    entity = "(" + " OR ".join(f'"{t}"' for t in terms) + ")"
    counts = {"any": europepmc_count(entity)}
    for key, topic in topics.items():
        counts[key] = europepmc_count(f"{entity} AND ({topic})")
    return {"query_entity": entity, "counts": counts}
