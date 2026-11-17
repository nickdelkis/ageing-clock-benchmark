# Ageing clock benchmark

A small target-discovery workflow for healthy ageing, built on public data in four parts:

1. **Biomarker.** Six epigenetic clocks on a public blood-methylation cohort: where they agree, and what a condition linked to shorter life does to them.
2. **Triage.** An LLM agent assesses the seven plasma proteins behind the GrimAge clock as candidate targets. It scores them from public evidence, and code checks every fact it cites.
3. **Direction.** Cis-Mendelian randomisation tests whether genetically higher levels of each protein shorten lifespan. The agent then reads those results as further evidence.
4. **Replication.** The clock analysis repeated in two larger cohorts and pooled, with the effect of one cohort's missing probes measured.

Of the five proteins that could be tested, only PAI-1 (SERPINE1) had causal support. With that evidence, the agent's proposal for PAI-1 changed from "unclear" to "inhibit". Across three cohorts, faster ageing in schizophrenia on DunedinPACE and GrimAge2 replicated, and only DunedinPACE kept part of it after adjusting for smoking.

## Part 1: clock benchmark

Epigenetic clocks are often treated as interchangeable measures of "biological age". Part 1 runs six published clocks on one public blood-methylation dataset to see where they agree, where they don't, and whether they register a condition linked to shorter life. The clocks are Horvath, Hannum, PhenoAge, GrimAge2, DunedinPACE and CausAge, run with [Biolearn](https://bio-learn.github.io/).

The dataset is GSE41169: whole blood on the Illumina 450K array, 62 people with schizophrenia and 33 controls.

Schizophrenia showed faster ageing on GrimAge2 (+4.3 years) and DunedinPACE (+7%), but not on the other four clocks. Both effects disappeared after adjusting for a methylation-based smoking score. This reproduces the result Shirai et al. (2024) reported for the same dataset. Larger cohorts still show a residual effect, which a sample of 95 is not powered to detect. Part 4 tests this.

![Effect of schizophrenia on each clock before and after adjusting for smoking and blood cells](results/fig4_adjustment_effect.png)

*Schizophrenia minus control, in SD units of age deviation (95% CI). Blue: adjusted for sex only. Orange: plus a methylation smoking score. Green: plus blood cell proportions. QC-passed samples.*

The full write-up, with methods and the literature comparison, is in [WRITEUP.md](WRITEUP.md).

| Figure | Shows |
| --- | --- |
| `results/fig1_predicted_vs_age.png` | Each clock against chronological age |
| `results/fig2_deviation_correlation.png` | How the clocks' age deviations correlate |
| `results/fig3_case_control_effect.png` | Effect of schizophrenia on each clock |
| `results/fig4_adjustment_effect.png` | That effect after adjusting for smoking and blood cells |

## Part 2: agentic target annotation

GrimAge is built from methylation surrogates of seven plasma proteins (ADM, B2M, cystatin C, GDF15, leptin, PAI-1, TIMP-1). `notebooks/target_ranking.ipynb` asks an LLM agent to assess them as candidate targets for healthy ageing, then checks its work:

- **Evidence is gathered without an LLM** from Open Targets, UniProt and Europe PMC, and cached in `targets/evidence/`.
- **The agent reads that evidence through tools** and scores ageing relevance, mechanism, tractability, safety and clinical precedence. It must cite the facts behind every score and list claims from its own knowledge separately.
- **Every citation is checked against the evidence.** The agent is also compared with a rule-based baseline and run several times to measure stability.

![Agent and rule-based ranking of the seven GrimAge proteins](results/fig5_target_ranking.png)

*Overall priority score per protein: agent mean with range across three runs (blue), rule-based baseline (orange diamond). Latest run, with the MR evidence from part 3: 264 of 265 cited facts matched the evidence.*

The agent works with Anthropic, OpenAI or a local model (e.g. Ollama): copy `.env.example` to `.env` and fill in one option. Details and results: part 2 of [WRITEUP.md](WRITEUP.md).

## Part 3: Mendelian randomisation

The agent in part 2 could not say whether to inhibit or activate most proteins. Part 3 tests whether genetically higher levels of each protein cause shorter lifespan, more frailty or faster GrimAge ageing, using cis-Mendelian randomisation on public GWAS summary statistics (R, in `mr/`).

- **Only PAI-1 (SERPINE1) showed a causal signal:** genetically higher PAI-1 meant shorter parental lifespan (p = 0.0015, Bonferroni-significant across 20 tests). The direction replicated in two other PAI-1 studies. Colocalisation was inconclusive because the lifespan GWAS is weak at this locus.
- **The other four testable proteins were null;** B2M and TIMP1 had no usable instruments.
- **The agent now reads these results** through an eighth tool. It changed its proposal for PAI-1 from "unclear" to "inhibit", recommended prioritising it in two of three runs, and lowered its scores for proteins with well-powered null results.

Details: part 3 of [WRITEUP.md](WRITEUP.md). Setup and scripts: [mr/README.md](mr/README.md).

## Part 4: replication in two larger cohorts

Part 4 runs the part 1 notebook on two larger whole-blood cohorts, GSE80417 (332 cases, 304 controls) and GSE84727 (260 cases, 405 controls), and pools all three with a random-effects meta-analysis.

- **Faster ageing on GrimAge2 and DunedinPACE replicated in every cohort:** pooled +4.8 years and +0.10 biological years per year (both p ≈ 0.01). The clocks trained on chronological age showed no consistent difference.
- **After adjusting for smoking and blood cells, DunedinPACE stayed elevated in both large cohorts,** but not in the small, young GSE41169, so the three-cohort pooled interval includes zero. GrimAge2's effect was mostly smoking.
- **Harmonising the data:**
  - the new cohorts' betas are only in GEO supplementary files, so they have their own loader;
  - two impossible ages (891 and 883 years) had to be removed;
  - GSE84727 was deposited without about 65,000 probes. Rerunning the other cohorts on its probe set showed that this shrinks the raw schizophrenia effect by a fifth to a third and leaves the smoking-adjusted effect unchanged.

![DunedinPACE: schizophrenia effect in three cohorts before and after adjustment](results/pooled/fig_pooled_DunedinPACE.png)

*Schizophrenia minus control in DunedinPACE, adjusted for sex (blue), plus a methylation smoking score (orange), plus blood cells (green). Cohorts with 95% CI; pooled random-effects estimate with Hartung–Knapp 95% CI.*

Details: part 4 of [WRITEUP.md](WRITEUP.md). Per-cohort results are in `results/<dataset>/`, the pooled ones in `results/pooled/`.

## Run it

Requires Docker.

```bash
docker compose build                       # once
docker compose run --rm clocks pytest -q   # optional: run the tests
docker compose up                          # open the http://127.0.0.1:8888 link it prints
```

Then run `notebooks/clock_benchmark.ipynb` (part 1) or `notebooks/target_ranking.ipynb` (part 2) top to bottom. The dataset downloads from GEO on the first run.

For part 4, run the clock notebook once per cohort, then pool them. The two larger cohorts download 2.4–2.7 GB each the first time.

```bash
for g in GSE41169 GSE80417 GSE84727; do
  docker compose run --rm -e CLOCK_DATASET=$g clocks jupyter nbconvert --to notebook --execute \
    --output-dir results/$g --output clock_benchmark_$g.ipynb notebooks/clock_benchmark.ipynb
done
docker compose run --rm clocks jupyter nbconvert --to notebook --execute --inplace notebooks/cohort_summary.ipynb
```

Part 3 runs in a second container with RStudio and needs a free OpenGWAS token in `.env`. `docker compose up` starts it at http://127.0.0.1:8787; run the scripts in `mr/` in order, then the part 2 notebook picks up their results. See [mr/README.md](mr/README.md).

## References

- Moqri M, et al. (2023) Biomarkers of aging for the identification and evaluation of longevity interventions. *Cell* 186:3758–3775. [doi:10.1016/j.cell.2023.08.003](https://doi.org/10.1016/j.cell.2023.08.003)
- Shirai T, et al. (2024) Meta-analyses of epigenetic age acceleration and GrimAge components of schizophrenia or first-episode psychosis. *Schizophrenia* 10:108. [doi:10.1038/s41537-024-00531-8](https://doi.org/10.1038/s41537-024-00531-8)
- Caspi A, et al. (2024) Accelerated pace of aging in schizophrenia: five case-control studies. *Biological Psychiatry* 95(11):1038–1047. [doi:10.1016/j.biopsych.2023.10.023](https://doi.org/10.1016/j.biopsych.2023.10.023)
- Hannon E, et al. (2016) An integrated genetic-epigenetic analysis of schizophrenia: evidence for co-localization of genetic associations and differential DNA methylation. *Genome Biology* 17:176. [doi:10.1186/s13059-016-1041-x](https://doi.org/10.1186/s13059-016-1041-x)
