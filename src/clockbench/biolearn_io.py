"""Thin, defensive wrappers around Biolearn.

Biolearn's model and dataset names, and some call signatures, have shifted
between releases. These helpers fail with a readable message (and close
matches) instead of a stack trace, so the notebook keeps running and simply
skips what isn't available in the installed version.
"""

from __future__ import annotations

import difflib
import time
from dataclasses import dataclass, field

import pandas as pd


def available_models() -> list[str]:
    """Names of the clocks the installed Biolearn knows about."""
    try:
        from biolearn.model import model_definitions  # type: ignore

        return sorted(model_definitions.keys())
    except Exception:
        pass
    try:
        from biolearn.model_gallery import ModelGallery  # type: ignore

        gallery = ModelGallery()
        for attr in ("models", "model_definitions"):
            names = getattr(gallery, attr, None)
            if names:
                return sorted(names)
    except Exception:
        pass
    return []


def available_datasets() -> list[str]:
    """IDs of the datasets in Biolearn's data library, if it exposes a list."""
    try:
        from biolearn.data_library import DataLibrary  # type: ignore

        lib = DataLibrary()
        for attr in ("sources", "lib_sources", "library"):
            items = getattr(lib, attr, None)
            if items:
                ids = [getattr(s, "id", s) for s in items]
                return sorted(str(i) for i in ids)
    except Exception:
        pass
    return []


def resolve_names(requested: list[str], available: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Match requested clock names to available ones, case-insensitively.

    Returns (resolved, missing): resolved maps requested -> actual name;
    missing maps requested -> close matches to try instead.
    """
    if not available:  # can't check; trust the request and let predict() fail per clock
        return {r: r for r in requested}, {}
    lower = {a.lower(): a for a in available}
    resolved, missing = {}, {}
    for name in requested:
        if name.lower() in lower:
            resolved[name] = lower[name.lower()]
        else:
            missing[name] = difflib.get_close_matches(name, available, n=4, cutoff=0.4)
    return resolved, missing


def load_dataset(dataset_id: str):
    """Download (first time only, cached) and load a GEO dataset.

    Datasets whose betas are only in a supplementary file (see
    geo_supplementary.SOURCES) go through this project's own loader;
    everything else through Biolearn's data library.
    """
    from .geo_supplementary import SOURCES, load_supplementary

    if dataset_id in SOURCES:
        return load_supplementary(dataset_id)

    from biolearn.data_library import DataLibrary  # type: ignore

    source = DataLibrary().get(dataset_id)
    if source is None:
        close = difflib.get_close_matches(dataset_id, available_datasets(), n=5, cutoff=0.5)
        raise KeyError(f"{dataset_id} is not in Biolearn's data library. Close matches: {close or 'none found'}")
    return source.load()


def find_column(metadata: pd.DataFrame, *candidates: str) -> str | None:
    """First metadata column whose name matches one of the candidates (case-insensitive)."""
    lower = {c.lower(): c for c in metadata.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def guess_condition_columns(metadata: pd.DataFrame, exclude: tuple[str, ...] = ("age", "sex")) -> dict[str, pd.Series]:
    """Metadata columns that look like a case/control label (2-6 distinct values)."""
    out = {}
    for col in metadata.columns:
        if col.lower() in exclude:
            continue
        counts = metadata[col].value_counts(dropna=True)
        if 2 <= len(counts) <= 6 and counts.min() >= 3:
            out[col] = counts
    return out


@dataclass
class ClockRun:
    predictions: pd.DataFrame
    seconds: dict[str, float] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)


def _first_numeric(out) -> pd.Series:
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


def run_clocks(data, clock_names: dict[str, str], imputation: str | None = None) -> ClockRun:
    """Run each clock on `data`; collect predictions, timings and failures.

    clock_names maps the label to use in results -> Biolearn model name.
    imputation is passed to ModelGallery.get() when the installed version
    supports it (e.g. "averaging"); otherwise Biolearn's default is used.
    """
    from biolearn.model_gallery import ModelGallery  # type: ignore

    gallery = ModelGallery()
    preds, seconds, failed = {}, {}, {}
    for label, model_name in clock_names.items():
        t0 = time.perf_counter()
        try:
            if imputation:
                try:
                    model = gallery.get(model_name, imputation_method=imputation)
                except TypeError:
                    model = gallery.get(model_name)
            else:
                model = gallery.get(model_name)
            preds[label] = _first_numeric(model.predict(data))
            seconds[label] = time.perf_counter() - t0
        except Exception as exc:  # keep going; report at the end
            failed[label] = f"{type(exc).__name__}: {exc}"
    return ClockRun(pd.DataFrame(preds), seconds, failed)


def encode_binary(series: pd.Series) -> pd.Series:
    """Encode a two-level variable (e.g. sex) as 0/1 for use as a covariate."""
    levels = sorted(series.dropna().unique(), key=str)
    if len(levels) != 2:
        raise ValueError(f"Expected 2 levels, got {levels}")
    return series.map({levels[0]: 0.0, levels[1]: 1.0})


def model_cpgs(gallery, model_names) -> set[str]:
    """Every CpG the given Biolearn models read, including DunedinPACE's normalisation set.

    Running the models on just these rows gives the same results as on the full
    matrix (imputation and DunedinPACE's normalisation work row by row or on
    their own CpG set) and needs a fraction of the memory.
    """
    from biolearn.util import get_data_file  # type: ignore

    sites: set[str] = set()
    for name in model_names:
        sites.update(str(s) for s in gallery.get(name).methylation_sites())
        if "dunedinpace" in name.lower():
            gold = pd.read_csv(get_data_file("DunedinPACE_Gold_Means.csv"), index_col=0)
            sites.update(gold.index.astype(str))
    return sites


def subset_cpgs(data, cpgs):
    """The same dataset with only the given CpGs (those present) kept."""
    from biolearn.data_library import GeoData  # type: ignore

    keep = data.dnam.index.intersection(pd.Index(sorted(cpgs)))
    return GeoData(data.metadata, data.dnam.loc[keep])


def subset_samples(data, samples):
    """The same dataset with only the given samples kept, metadata and betas aligned."""
    from biolearn.data_library import GeoData  # type: ignore

    samples = list(samples)
    return GeoData(data.metadata.loc[samples], data.dnam[samples])


def sex_probe_coverage(dnam: pd.DataFrame) -> dict[str, float]:
    """Share of the sex estimator's X and Y probes present in the data."""
    from biolearn.util import get_data_file  # type: ignore

    ref = pd.read_csv(get_data_file("estimateSex.csv"), usecols=["IlmnID", "CHR"], low_memory=False)
    out = {}
    for chrom in ("X", "Y"):
        probes = ref.loc[ref["CHR"] == chrom, "IlmnID"]
        out[chrom] = float(probes.isin(dnam.index).mean())
    return out
