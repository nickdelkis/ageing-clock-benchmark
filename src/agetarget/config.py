"""Every setting of the analysis in one place: paths, cohorts, clocks and targets."""

from __future__ import annotations

from pathlib import Path

# ---- Paths ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"                       # downloads and caches, never committed
RESULTS = ROOT / "results"
CLOCK_RESULTS = RESULTS / "clocks"             # one folder per cohort, plus pooled/
TARGET_RESULTS = RESULTS / "targets"
EVIDENCE_DIR = TARGET_RESULTS / "evidence"     # cached API responses, one JSON per target
AGENT_RUNS = TARGET_RESULTS / "agent_runs"     # one folder per batch of agent runs
MR_RESULTS = RESULTS / "mr"                    # written by the R scripts in mr/

# ---- Cohorts --------------------------------------------------------------------
# Whole-blood Illumina 450K, schizophrenia vs control. `exclude` lists samples dropped
# from the QC-passed analysis besides sex mismatches.
COHORTS = {
    "GSE41169": {"exclude": ["GSM1009696"]},   # four clocks put it 14-21 years below its recorded age
    "GSE80417": {"exclude": []},
    "GSE84727": {"exclude": []},
}
DISEASE_LABELS = {1.0: "control", 2.0: "schizophrenia"}   # the same coding in all three cohorts
CASE, CONTROL = "schizophrenia", "control"

# Recorded ages outside this range are data-entry errors (GSE80417 has ages of 891 and 883)
AGE_RANGE = (0, 110)
# Run the methylation sex check only if this share of the estimator's X and Y probes is present
SEX_CHECK_MIN = {"X": 0.5, "Y": 0.1}
# CpGs a model needs but a dataset lacks are filled from Biolearn's 450K reference medians
IMPUTATION = "sesame_450k"
# Rerun the clocks on only this cohort's probes, to measure what its missing probes do
SENSITIVITY_PROBES = "GSE84727"

# ---- Clocks ---------------------------------------------------------------------
# label -> (Biolearn model, kind). "age" = biological age in years, "pace" = rate of ageing.
CLOCKS = {
    "Horvath": ("Horvathv1", "age"),         # trained on chronological age
    "Hannum": ("Hannum", "age"),             # trained on chronological age
    "PhenoAge": ("PhenoAge", "age"),         # trained on a clinical phenotype
    "GrimAge2": ("GrimAgeV2", "age"),        # trained on time to death
    "DunedinPACE": ("DunedinPACE", "pace"),  # trained on pace of physiological decline
    "CausAge": ("YingCausAge", "age"),       # CpGs with putative causal links to ageing
}
SMOKING_MODEL = "SmokingMcCartney"
CELL_MODEL = "DeconvoluteBlood450K"
CELL_COVARIATES = ["b_cell", "cd4_t_cell", "cd8_t_cell", "monocyte"]
COVARIATE_MODELS = {   # name -> label in figures; each adds covariates to the previous one
    "sex": "Sex",
    "sex+smoking": "+ smoking score",
    "sex+smoking+cells": "+ smoking + blood cells",
}
CLOCK_ORDER = ["Horvath", "Hannum", "PhenoAge", "CausAge", "DunedinPACE", "GrimAge2"]   # bottom to top in figures
HIGHLIGHT = {"GrimAge2", "DunedinPACE"}
UNITS = {"DunedinPACE": "biological years per year"}   # every other clock: years

# ---- Targets ----------------------------------------------------------------------
# Context shown to the agent. Each sentence says exactly what a finding applies to, so the
# agent does not transfer a clock-level result to an individual protein. Kept word for word
# as the saved batches saw it.
_GRIM = ("One of seven plasma proteins whose DNA-methylation surrogates make up the GrimAge clock. "
         "Part 1 of this project: the GrimAge clock as a whole was +4.3 years older in schizophrenia, a difference "
         "that disappeared after adjusting for a methylation smoking score; this protein's own surrogate was not tested. "
         "Surrogates are methylation estimates, not measured protein levels.")
_UP = (" Shirai et al. 2024 (7-cohort meta-analysis): this protein's DNAm surrogate was higher in schizophrenia or "
       "first-episode psychosis in a model adjusted for age, sex and DNAm smoking pack-years.")
_NS = (" Shirai et al. 2024 (7-cohort meta-analysis): this protein's DNAm surrogate did not differ significantly in "
       "the main model adjusted for age, sex and DNAm smoking pack-years.")

# symbol -> context shown to the agent, and literature search terms.
# Curated names avoid ambiguous symbols (e.g. "ADM", "LEP") inflating publication counts.
TARGETS = {
    "ADM": {"context": _GRIM + _UP, "aliases": ["adrenomedullin", "proadrenomedullin", "MR-proADM"]},
    "B2M": {"context": _GRIM + _UP, "aliases": ["beta-2-microglobulin", "beta2-microglobulin", "beta 2 microglobulin"]},
    "CST3": {"context": _GRIM + _UP, "aliases": ["cystatin C", "cystatin-C"]},
    "SERPINE1": {"context": _GRIM + _UP, "aliases": ["plasminogen activator inhibitor-1", "plasminogen activator inhibitor 1",
                                                     "PAI-1", "SERPINE1"]},
    "GDF15": {"context": _GRIM + _NS, "aliases": ["GDF15", "GDF-15", "growth differentiation factor 15",
                                                  "growth differentiation factor-15"]},
    "LEP": {"context": _GRIM + _NS, "aliases": ["leptin"]},
    "TIMP1": {"context": _GRIM + _NS, "aliases": ["TIMP-1", "TIMP1", "tissue inhibitor of metalloproteinases-1",
                                                  "tissue inhibitor of metalloproteinase 1"]},
}
N_RUNS = 3   # agent assessments per target, to measure stability
