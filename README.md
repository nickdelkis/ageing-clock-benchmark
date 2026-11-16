# Ageing clock benchmark

A small, contained benchmark of published epigenetic ageing clocks on one public blood-methylation dataset, using [Biolearn](https://bio-learn.github.io/).

It asks three questions, framed by the biomarker criteria in Moqri et al. 2023 (*Cell*, [doi:10.1016/j.cell.2023.08.003](https://doi.org/10.1016/j.cell.2023.08.003)):

1. How well does each clock track chronological age? (context, not the goal)
2. Do the clocks agree on *who* is ageing fast?
3. Does each clock register a condition known to shorten life?

Default dataset: **GSE41169**, whole blood on the Illumina 450K array, schizophrenia cases and controls. Default clocks: Horvath, Hannum, PhenoAge, GrimAge2, DunedinPACE and the causal clock CausAge.

## What "contained" means here

- Everything runs in one Docker container built from `requirements.txt`. Nothing is installed on your machine.
- The container sees only this project folder (mounted at `/work`). The Biolearn download cache and Jupyter settings live in `.home/` inside it, so deleting the folder removes every trace.
- Jupyter listens on `127.0.0.1:8888` only, so it is not reachable from your network.
- It runs as a normal user, not root, and memory is capped at 12 GB.

## Requirements

- Docker Desktop (Windows/macOS) or Docker Engine with the compose plugin (Linux).
- About 3 GB of disk: ~1.5 GB for the image, the rest for the GEO download.
- 8 GB RAM is enough for GSE41169 (~95 samples). Larger datasets need more.

## Run it

```bash
# 1. Build the image (once, ~5 min)
docker compose build

# Linux only: make files written by the container belong to you
#   export UID GID=$(id -g) && docker compose build

# 2. Check the statistics code (should print "9 passed")
docker compose run --rm clocks pytest -q

# 3. Start Jupyter, then open the http://127.0.0.1:8888/lab?token=... link it prints
docker compose up
```

Open `notebooks/clock_benchmark.ipynb` and run all cells. The first run downloads the dataset from GEO (a few minutes); later runs use the cache.

To run without opening Jupyter and get an HTML report instead:

```bash
docker compose run --rm clocks jupyter nbconvert --to html --execute \
  notebooks/clock_benchmark.ipynb --output-dir results
```

Stop Jupyter with `Ctrl+C`, then `docker compose down`.

## Outputs (in `results/`)

| File | What it is |
| --- | --- |
| `fig1_predicted_vs_age.png` | Each clock against chronological age, coloured by group |
| `fig2_deviation_correlation.png` | Correlation of age deviations between clocks |
| `fig3_case_control_effect.png` | Effect size of the condition per clock, with 95% CI |
| `clock_metrics.csv` | r, MAE, bias per clock |
| `age_deviation_per_sample.csv` | Residual age deviation, samples x clocks |
| `age_deviation_correlations.csv` | The matrix behind figure 2 |
| `case_control.csv` | Group means, difference, Cohen's d, p and BH q, sex-adjusted estimates |
| `environment.txt` | Exact package versions used |

## Changing things

All options are in the first notebook cell.

- **Clocks.** Edit `CLOCKS`. Section 1 of the notebook lists every clock the installed Biolearn has; names are matched case-insensitively and unknown names are skipped with close matches suggested.
- **Dataset.** Change `DATASET` to another GEO ID in Biolearn's library. It must have age in its metadata.
- **Case/control.** The notebook guesses the label column and which level is the control. It prints its guess; if it's wrong, set `CONDITION_COL`, `CASE` and `CONTROL`.

## Known rough edges

- **Biolearn names and signatures change between versions.** The wrappers in `src/clockbench/biolearn_io.py` catch this and skip a clock rather than crash. Check the "FAILED" lines in section 3.
- **GrimAge needs sex and age** in the format Biolearn expects. If it fails, check how `sex` is coded in the metadata, or drop it.
- **Missing CpGs are imputed.** The 450K array lacks some CpGs a few clocks use. `IMPUTATION = "averaging"` fills them from reference means if your Biolearn version supports it.
- **No cell-composition adjustment.** Blood cell proportions shift with age, smoking and medication, and some clocks move with them. This is the first thing a reviewer would ask about; name it as a limitation.

## Layout

```
├── Dockerfile, docker-compose.yml, requirements.txt
├── notebooks/clock_benchmark.ipynb   the analysis
├── src/clockbench/
│   ├── analysis.py      age deviation, metrics, correlations, case/control stats
│   ├── biolearn_io.py   defensive wrappers around Biolearn
│   └── plots.py         the three figures
├── tests/test_analysis.py   statistics checked on synthetic data with known answers
├── WRITEUP.md           one-page findings template
└── results/             outputs (git-ignored except what you choose to commit)
```

## References

- Moqri M, et al. (2023) Biomarkers of aging for the identification and evaluation of longevity interventions. *Cell* 186:3758–3775.
- Biolearn: Ying K, et al. (2024) Biolearn, an open-source library for biomarkers of aging.
- ComputAgeBench: Kriukov D, et al. (2025) KDD '25.
