"""Checks of the supplementary-betas loader on small synthetic GEO files.

No network: the files are written to a temporary folder, where download()
finds them and skips fetching.
"""

import gzip

import numpy as np
import pandas as pd
import pytest

from clockbench.geo_supplementary import (
    SOURCES,
    SupplementarySource,
    parse_series_matrix,
    read_betas,
    standardise_metadata,
)

GSMS = ["GSM1", "GSM2", "GSM3", "GSM4"]
SENTRIX = ["100_R01C01", "100_R02C01", "200_R01C01", "200_R02C01"]


def write_matrix(path, sources=None, codes=None, sex=None, sentrix_row="description"):
    sources = sources or ["control blood", "case blood", "control blood", "case blood"]
    codes = codes or ["1", "2", "1", "2"]
    sex = sex or ["M", "F", "F", "M"]

    def row(key, values):
        return "\t".join([key] + [f'"{v}"' for v in values])

    lines = [
        '!Series_title\t"A test series"',
        row("!Sample_title", ["C1", "S1", "C2", "S2"]),
        row("!Sample_geo_accession", GSMS),
        row("!Sample_source_name_ch1", sources),
        row("!Sample_characteristics_ch1", [f"Sex: {s}" for s in sex]),
        row("!Sample_characteristics_ch1", ["age: 23", "age: 57.5", "age: 40", "age: NA"]),
        row("!Sample_characteristics_ch1", [f"disease status: {c}" for c in codes]),
    ]
    if sentrix_row == "description":
        lines.append(row("!Sample_description", SENTRIX))
    else:
        lines.append(row("!Sample_characteristics_ch1", [f"sentrixids: {s}" for s in SENTRIX]))
    lines += ["!series_matrix_table_begin", '"ID_REF"\t' + "\t".join(f'"{g}"' for g in GSMS),
              "!series_matrix_table_end"]
    with gzip.open(path, "wt") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_betas(path, columns=SENTRIX):
    rng = np.random.default_rng(1)
    df = pd.DataFrame(rng.uniform(0, 1, (5, len(columns))), columns=columns,
                      index=[f"cg0000000{i}" for i in range(5)])
    df.iloc[0, 0] = np.nan
    df.to_csv(path, compression="gzip")
    return df


SOURCE = SupplementarySource(betas_file="x.csv.gz", sentrix_field="description", disease_field="disease status")


def test_parse_series_matrix_reads_characteristics(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz"))
    assert list(raw.index) == GSMS
    assert raw.loc["GSM2", "age"] == "57.5"
    assert raw.loc["GSM1", "description"] == SENTRIX[0]
    assert {"title", "source_name", "Sex", "disease status"} <= set(raw.columns)


def test_standardise_codes_sex_age_and_disease(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz"))
    meta, _ = standardise_metadata(raw, SOURCE)
    assert meta["sex"].tolist() == [1.0, 0.0, 0.0, 1.0]  # 0 = female, 1 = male
    assert meta.loc["GSM2", "age"] == 57.5 and np.isnan(meta.loc["GSM4", "age"])
    assert meta["disease"].tolist() == [1.0, 2.0, 1.0, 2.0]  # 1 = control, as in GSE41169
    assert "Sex" not in meta.columns  # no "Sex"/"sex" ambiguity


def test_disease_label_follows_source_name_even_if_codes_are_flipped(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz", codes=["2", "1", "2", "1"]))
    meta, _ = standardise_metadata(raw, SOURCE)
    assert meta["disease"].tolist() == [1.0, 2.0, 1.0, 2.0]


def test_disagreeing_disease_code_raises(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz", codes=["1", "2", "2", "2"]))
    with pytest.raises(ValueError, match="does not match"):
        standardise_metadata(raw, SOURCE)


def test_unknown_sex_value_raises(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz", sex=["M", "F", "U", "M"]))
    with pytest.raises(ValueError, match="sex"):
        standardise_metadata(raw, SOURCE)


def test_sentrix_from_characteristic(tmp_path):
    raw = parse_series_matrix(write_matrix(tmp_path / "m.txt.gz", sentrix_row="characteristic"))
    source = SupplementarySource("x.csv.gz", sentrix_field="sentrixids", disease_field="disease status")
    meta, _ = standardise_metadata(raw, source)
    assert meta["sentrix_id"].tolist() == SENTRIX


def test_read_betas_maps_sentrix_to_gsm(tmp_path):
    shuffled = [SENTRIX[i] for i in (2, 0, 3, 1)]  # file order differs from metadata order
    original = write_betas(tmp_path / "b.csv.gz", columns=shuffled)
    betas = read_betas(tmp_path / "b.csv.gz", pd.Series(GSMS, index=SENTRIX), chunksize=2)
    assert betas.dtypes.unique().tolist() == [np.float32]
    assert betas.shape == (5, 4) and betas.index[0] == "cg00000000"
    # The column that was Sentrix 200_R01C01 must now be GSM3, with the same values
    assert np.allclose(betas["GSM3"].iloc[1:], original["200_R01C01"].iloc[1:], atol=1e-6)
    assert np.isnan(betas["GSM3"].iloc[0])


def test_read_betas_refuses_unmatched_samples(tmp_path):
    write_betas(tmp_path / "b.csv.gz", columns=SENTRIX[:3] + ["999_R01C01"])
    with pytest.raises(ValueError, match="no sample in the metadata"):
        read_betas(tmp_path / "b.csv.gz", pd.Series(GSMS, index=SENTRIX))


def test_load_supplementary_end_to_end(tmp_path):
    pytest.importorskip("biolearn")
    from clockbench.geo_supplementary import load_supplementary

    gse = "GSE80417"
    folder = tmp_path / gse
    folder.mkdir()
    write_matrix(folder / f"{gse}_series_matrix.txt.gz")
    write_betas(folder / SOURCES[gse].betas_file, columns=SENTRIX[::-1])
    data = load_supplementary(gse, data_dir=tmp_path, verbose=False)
    assert list(data.dnam.columns) == GSMS == list(data.metadata.index)
    assert (folder / f"{gse}_betas_float32.pkl").exists()  # cached for the next load

    from clockbench.geo_supplementary import probe_ids
    assert list(probe_ids(gse, data_dir=tmp_path)) == [f"cg0000000{i}" for i in range(5)]


def test_subset_helpers_keep_metadata_and_betas_aligned(tmp_path):
    pytest.importorskip("biolearn")
    from biolearn.data_library import GeoData
    from clockbench.biolearn_io import subset_cpgs, subset_samples

    meta = pd.DataFrame({"age": [30.0, 40.0, 50.0]}, index=["A", "B", "C"])
    dnam = pd.DataFrame(np.arange(12.0).reshape(4, 3), index=["cg1", "cg2", "cg3", "cg4"], columns=["A", "B", "C"])
    data = GeoData(meta, dnam)
    sub = subset_cpgs(data, {"cg2", "cg4", "cg_absent"})
    assert list(sub.dnam.index) == ["cg2", "cg4"] and sub.dnam.shape[1] == 3
    kept = subset_samples(data, ["C", "A"])
    assert list(kept.metadata.index) == list(kept.dnam.columns) == ["C", "A"]
