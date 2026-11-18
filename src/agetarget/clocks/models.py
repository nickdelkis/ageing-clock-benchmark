"""Biolearn models: the clocks, the smoking score, blood cell proportions and the sex check."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from functools import cache

import pandas as pd

from ..config import CELL_MODEL, IMPUTATION, SMOKING_MODEL


@cache
def gallery():
    from biolearn.model_gallery import ModelGallery  # type: ignore

    return ModelGallery()


@dataclass
class ClockRun:
    predictions: pd.DataFrame
    seconds: dict[str, float] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)


def _estimate(out) -> pd.Series:
    """The clock's estimate from a model's output. GrimAge also returns its
    protein and smoking surrogates, so never take the first column blindly."""
    if isinstance(out, pd.Series):
        return out.astype(float)
    cols = list(out.columns)
    lower = {str(c).lower(): c for c in cols}
    if "predicted" in lower:
        return out[lower["predicted"]].astype(float)
    grim = [c for c in cols if "grimage" in str(c).lower() and "accel" not in str(c).lower()]
    if len(grim) == 1:
        return out[grim[0]].astype(float)
    numeric = out.select_dtypes("number").columns
    if len(numeric) == 1:
        return out[numeric[0]].astype(float)
    raise ValueError(f"Several output columns, not sure which is the estimate: {cols}")


def run_clocks(data, clocks: dict[str, str], imputation: str = IMPUTATION) -> ClockRun:
    """Run each clock (label -> Biolearn model name); collect estimates, timings and failures."""
    preds, seconds, failed = {}, {}, {}
    for label, model_name in clocks.items():
        t0 = time.perf_counter()
        try:
            preds[label] = _estimate(gallery().get(model_name, imputation_method=imputation).predict(data))
            seconds[label] = time.perf_counter() - t0
        except Exception as exc:  # keep going; the caller reports failures
            failed[label] = f"{type(exc).__name__}: {exc}"
    return ClockRun(pd.DataFrame(preds), seconds, failed)


def smoking_score(data, imputation: str = IMPUTATION) -> pd.Series:
    """McCartney's methylation smoking score, one value per sample."""
    return gallery().get(SMOKING_MODEL, imputation_method=imputation).predict(data)["Predicted"].rename("smoking")


def cell_proportions(data) -> pd.DataFrame:
    """Blood cell proportions estimated from methylation (Reinius reference)."""
    return gallery().get(CELL_MODEL).predict(data)


def predicted_sex(data) -> pd.DataFrame:
    """Biolearn's methylation sex estimate. Needs the full matrix: it standardises over all autosomal probes."""
    return gallery().get("SexEstimation").predict(data)


def model_cpgs(model_names) -> set[str]:
    """Every CpG the given models read, including DunedinPACE's normalisation set.

    Running the models on just these rows gives the same results as on the full matrix
    (imputation works per CpG and DunedinPACE normalises over its own set) with a
    fraction of the memory.
    """
    from biolearn.util import get_data_file  # type: ignore

    sites: set[str] = set()
    for name in model_names:
        sites.update(str(s) for s in gallery().get(name).methylation_sites())
        if "dunedinpace" in name.lower():
            gold = pd.read_csv(get_data_file("DunedinPACE_Gold_Means.csv"), index_col=0)
            sites.update(gold.index.astype(str))
    return sites


def sex_probe_coverage(dnam: pd.DataFrame) -> dict[str, float]:
    """Share of the sex estimator's X and Y probes present in the data."""
    from biolearn.util import get_data_file  # type: ignore

    ref = pd.read_csv(get_data_file("estimateSex.csv"), usecols=["IlmnID", "CHR"], low_memory=False)
    return {chrom: float(ref.loc[ref["CHR"] == chrom, "IlmnID"].isin(dnam.index).mean()) for chrom in ("X", "Y")}
