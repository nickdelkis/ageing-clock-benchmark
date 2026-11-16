# Ageing clock benchmark

Epigenetic clocks are often treated as interchangeable measures of "biological age". This small project runs six published clocks on one public blood-methylation dataset to see where they agree, where they don't, and whether they register a condition linked to shorter life. The clocks are Horvath, Hannum, PhenoAge, GrimAge2, DunedinPACE and CausAge, run with [Biolearn](https://bio-learn.github.io/).

The dataset is GSE41169: whole blood on the Illumina 450K array, 62 people with schizophrenia and 33 controls.

## Result

Schizophrenia showed faster ageing on GrimAge2 (+4.3 years) and DunedinPACE (+7%), but not on the other four clocks. Both effects disappeared after adjusting for a methylation-based smoking score. This reproduces the result Shirai et al. (2024) reported for the same dataset. Larger cohorts still show a residual effect, which a sample of 95 is not powered to detect.

![Effect of schizophrenia on each clock before and after adjusting for smoking and blood cells](results/fig4_adjustment_effect.png)

*Schizophrenia minus control, in SD units of age deviation (95% CI). Blue: adjusted for sex only. Orange: plus a methylation smoking score. Green: plus blood cell proportions. QC-passed samples.*

The full write-up, with methods and the literature comparison, is in [WRITEUP.md](WRITEUP.md).

| Figure | Shows |
| --- | --- |
| `results/fig1_predicted_vs_age.png` | Each clock against chronological age |
| `results/fig2_deviation_correlation.png` | How the clocks' age deviations correlate |
| `results/fig3_case_control_effect.png` | Effect of schizophrenia on each clock |
| `results/fig4_adjustment_effect.png` | That effect after adjusting for smoking and blood cells |

## Run it

Requires Docker.

```bash
docker compose build                       # once
docker compose run --rm clocks pytest -q   # optional: 9 tests
docker compose up                          # open the http://127.0.0.1:8888 link it prints
```

Then run `notebooks/clock_benchmark.ipynb` top to bottom. The dataset downloads from GEO on the first run.

## References

- Moqri M, et al. (2023) Biomarkers of aging for the identification and evaluation of longevity interventions. *Cell* 186:3758–3775. [doi:10.1016/j.cell.2023.08.003](https://doi.org/10.1016/j.cell.2023.08.003)
- Shirai T, et al. (2024) Meta-analyses of epigenetic age acceleration and GrimAge components of schizophrenia or first-episode psychosis. *Schizophrenia* 10:108. [doi:10.1038/s41537-024-00531-8](https://doi.org/10.1038/s41537-024-00531-8)
- Caspi A, et al. (2023) Accelerated pace of aging in schizophrenia: five case-control studies. *Biological Psychiatry* 95:1038–1047. [doi:10.1016/j.biopsych.2023.10.023](https://doi.org/10.1016/j.biopsych.2023.10.023)
