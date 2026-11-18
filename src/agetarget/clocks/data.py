"""Load a cohort as one object: sample metadata plus a CpG x sample beta matrix.

GSE41169 comes from Biolearn's data library. For GSE80417 and GSE84727 the GEO
series matrix holds metadata only and the normalised betas are in a supplementary
CSV with Sentrix chip positions as column names; this module downloads both files
once, maps chip positions to GSM accessions and returns the same structure as
Biolearn's curated datasets:

- metadata indexed by GSM, with numeric ``age``, ``sex`` (0 = female,
  1 = male) and ``disease`` (1 = control, 2 = case, as in GSE41169);
- betas as float32, CpGs x samples, columns in metadata order.

Parsed betas are cached in data/, so later loads take seconds.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import DATA_DIR

GEO_FTP = "https://ftp.ncbi.nlm.nih.gov/geo/series"


@dataclass(frozen=True)
class SupplementarySource:
    betas_file: str  # supplementary file name on GEO
    sentrix_field: str  # where the series matrix keeps each sample's Sentrix ID
    disease_field: str  # characteristic holding the 1/2 disease code


SOURCES = {
    "GSE80417": SupplementarySource(
        betas_file="GSE80417_normalizedBetas.csv.gz",
        sentrix_field="description",
        disease_field="disease status",
    ),
    "GSE84727": SupplementarySource(
        betas_file="GSE84727_normalisedBetas.csv.gz",
        sentrix_field="sentrixids",
        disease_field="disease_status",
    ),
}


def _series_dir(gse: str) -> str:
    return f"{GEO_FTP}/{gse[:-3]}nnn/{gse}"


def matrix_url(gse: str) -> str:
    return f"{_series_dir(gse)}/matrix/{gse}_series_matrix.txt.gz"


def betas_url(gse: str) -> str:
    return f"{_series_dir(gse)}/suppl/{SOURCES[gse].betas_file}"


def download(url: str, dest: Path) -> Path:
    """Download once; a partial download is never mistaken for a finished one."""
    if dest.exists():
        return dest
    import requests

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    print(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(part, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    part.rename(dest)
    return dest


# ---- metadata -----------------------------------------------------------------


def _split(line: str) -> list[str]:
    return [x.strip().strip('"') for x in line.rstrip("\n").split("\t")]


def parse_series_matrix(path: Path) -> pd.DataFrame:
    """Sample annotation from a series matrix, one row per GSM, raw strings.

    Columns: title, source_name, description, plus one column per
    characteristic, named by its key (e.g. "Sex", "age", "sentrixids").
    """
    fields: dict[str, list[str]] = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("!series_matrix_table_begin"):
                break
            if not line.startswith("!Sample_"):
                continue
            key, *values = _split(line)
            key = key.removeprefix("!Sample_")
            if key == "characteristics_ch1":
                keys = {v.split(":", 1)[0].strip() for v in values if ":" in v}
                if len(keys) != 1:
                    raise ValueError(f"A characteristics row mixes keys: {sorted(keys)}")
                name = keys.pop()
                fields[name] = [v.split(":", 1)[1].strip() if ":" in v else "" for v in values]
            elif key in ("geo_accession", "title", "source_name_ch1", "description"):
                fields[key.removesuffix("_ch1")] = values
    if "geo_accession" not in fields:
        raise ValueError(f"No !Sample_geo_accession row in {path}")
    return pd.DataFrame(fields).set_index("geo_accession").rename_axis("id")


def standardise_metadata(raw: pd.DataFrame, source: SupplementarySource) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add numeric age, sex and disease columns in Biolearn's coding.

    Disease labels come from the source name ("control blood" vs the other
    one) and must agree exactly with the 1/2 code in the characteristic;
    otherwise this raises. Returns (metadata, crosstab of the two).
    """
    meta = raw.copy()
    meta["age"] = pd.to_numeric(meta["age"], errors="coerce")
    sex = meta["Sex"].str.strip().str.upper().map({"F": 0.0, "M": 1.0, "FEMALE": 0.0, "MALE": 1.0})
    if sex.isna().any():
        bad = sorted(meta.loc[sex.isna(), "Sex"].unique())
        raise ValueError(f"Unrecognised sex values: {bad}")
    # Keep the raw label under another name: a "Sex" and a "sex" column would be ambiguous
    meta = meta.rename(columns={"Sex": "sex_recorded"})
    meta["sex"] = sex

    names = meta["source_name"].str.strip().str.lower()
    if names.nunique() != 2 or not names.str.contains("control").any():
        raise ValueError(f"Expected two source names, one of them a control: {sorted(names.unique())}")
    is_control = names.str.contains("control")
    code = pd.to_numeric(meta[source.disease_field], errors="coerce")
    table = pd.crosstab(meta["source_name"], code)
    control_codes = set(code[is_control].unique())
    case_codes = set(code[~is_control].unique())
    if len(control_codes) != 1 or len(case_codes) != 1 or control_codes == case_codes:
        raise ValueError(f"Disease code does not match the source names:\n{table}")
    meta["disease"] = np.where(is_control, 1.0, 2.0)
    meta["sentrix_id"] = meta[source.sentrix_field].str.strip()
    if meta["sentrix_id"].duplicated().any():
        raise ValueError("Duplicate Sentrix IDs in the series matrix")
    return meta, table


# ---- betas --------------------------------------------------------------------


def read_betas(path: Path, sentrix_to_gsm: pd.Series, chunksize: int = 20_000) -> pd.DataFrame:
    """Read a CpG x Sentrix-ID CSV in chunks as float32, with GSM column names.

    Every column must map to a sample in the metadata and vice versa.
    """
    with pd.read_csv(path, index_col=0, chunksize=chunksize) as reader:
        chunks = [chunk.astype(np.float32) for chunk in reader]
    betas = pd.concat(chunks)
    betas.index = betas.index.astype(str)
    betas.index.name = "id"

    cols = pd.Index(betas.columns.astype(str).str.strip())
    unmapped = cols.difference(sentrix_to_gsm.index)
    missing = sentrix_to_gsm.index.difference(cols)
    if len(unmapped) or len(missing):
        raise ValueError(
            f"{len(unmapped)} beta columns have no sample in the metadata (e.g. {list(unmapped[:3])}); "
            f"{len(missing)} samples have no beta column (e.g. {list(missing[:3])})"
        )
    betas.columns = sentrix_to_gsm.loc[cols].to_numpy()
    return betas


def summarise(betas: pd.DataFrame) -> dict[str, float]:
    values = betas.to_numpy()
    return {
        "cpgs": betas.shape[0],
        "samples": betas.shape[1],
        "missing_fraction": float(np.isnan(values).mean()),
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
    }


# ---- entry point --------------------------------------------------------------


def load_supplementary(gse: str, data_dir: Path | str = DATA_DIR, verbose: bool = True):
    """Download (first time only), parse and cache one dataset; return a GeoData."""
    from biolearn.data_library import GeoData  # type: ignore

    if gse not in SOURCES:
        raise KeyError(f"No supplementary loader for {gse}. Known: {sorted(SOURCES)}")
    source = SOURCES[gse]
    folder = Path(data_dir) / gse

    matrix = download(matrix_url(gse), folder / f"{gse}_series_matrix.txt.gz")
    meta, table = standardise_metadata(parse_series_matrix(matrix), source)

    cache = folder / f"{gse}_betas_float32.pkl"
    if cache.exists():
        betas = pd.read_pickle(cache)
    else:
        raw = download(betas_url(gse), folder / source.betas_file)
        if verbose:
            print(f"Parsing {raw.name} (a few minutes, once)")
        sentrix_to_gsm = pd.Series(meta.index, index=meta["sentrix_id"])
        betas = read_betas(raw, sentrix_to_gsm)
        betas.to_pickle(cache)
    betas = betas[meta.index]
    probes_file = folder / f"{gse}_probes.txt"
    if not probes_file.exists():
        probes_file.write_text("\n".join(betas.index) + "\n")

    if verbose:
        print(f"{gse}: disease code vs source name\n{table}\n")
        print({k: round(v, 4) if isinstance(v, float) else v for k, v in summarise(betas).items()})
    return GeoData(meta, betas)


def probe_ids(gse: str, data_dir: Path | str = DATA_DIR) -> pd.Index:
    """CpGs present in a dataset loaded with load_supplementary (written on first load)."""
    probes_file = Path(data_dir) / gse / f"{gse}_probes.txt"
    if not probes_file.exists():
        load_supplementary(gse, data_dir=data_dir, verbose=False)
    return pd.Index(probes_file.read_text().split(), name="id")


# ---- One entry point for every cohort -----------------------------------------


def load_dataset(dataset_id: str):
    """Load a cohort: this project's loader for SOURCES, Biolearn's data library otherwise."""
    if dataset_id in SOURCES:
        return load_supplementary(dataset_id)
    from biolearn.data_library import DataLibrary  # type: ignore

    source = DataLibrary().get(dataset_id)
    if source is None:
        raise KeyError(f"{dataset_id} is neither in SOURCES nor in Biolearn's data library")
    return source.load()


def find_column(metadata: pd.DataFrame, *candidates: str) -> str | None:
    """First metadata column whose name matches one of the candidates (case-insensitive)."""
    lower = {c.lower(): c for c in metadata.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


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
