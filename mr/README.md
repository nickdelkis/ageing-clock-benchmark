# Mendelian randomisation (part 3)

Goal: test whether genetically higher levels of each candidate protein *cause* faster epigenetic ageing or shorter lifespan. This uses public GWAS summary statistics only. The MR estimate gives the direction of effect (inhibit or activate), which the agent in part 2 often could not decide. The results feed the agent from part 2 through an eighth evidence tool, `get_causal_evidence`.

Runs in its own container (R + RStudio Server) next to the Python one, on the same project folder.

## One-time setup

1. **OpenGWAS token.** Sign in at <https://api.opengwas.io> (GitHub, Microsoft or email), open your profile and generate a token. It is free; usage draws on an allowance that refills periodically. Add it to `.env` in the project folder:

   ```
   OPENGWAS_JWT=eyJ...
   ```

2. **Build the R image** (once, roughly 10–20 minutes):

   ```
   docker compose build mr
   ```

   The last build step prints `R packages OK`. If it fails, copy the last 30 lines of output.

## Each session

```
docker compose up
```

This starts both containers. Then open:

- **RStudio:** <http://127.0.0.1:8787>. There is no login screen; it is only reachable from your own computer.
- **Jupyter:** <http://127.0.0.1:8888>, as before.

In RStudio, the project is the `work` folder. Set it as the working directory with *Session → Set Working Directory → Choose Directory → work*. Every script expects that.

## Steps

1. **`mr/00_check_setup.R`: check the token and find datasets.** It writes:
   - `results/opengwas_outcome_candidates.csv`: lifespan, healthspan, frailty and epigenetic-clock GWAS hosted on OpenGWAS, largest first;
   - `results/opengwas_pqtl_candidates.csv`: pQTL datasets that mention the seven proteins.

   Pick one pQTL study that covers as many of the proteins as possible (ideally all from one study), and two or three outcomes (e.g. parental lifespan, GrimAge acceleration). Check that the `build` column says GRCh37 / hg19.

2. **`mr/01_cis_mr_pilot.R`: the pilot.** Paste the ids into `EXPOSURE_IDS` and `OUTCOME_IDS` at the top and run it. For each protein it:
   - takes genome-wide significant, clumped variants for the protein;
   - keeps only those within ±1 Mb of the gene (cis instruments);
   - looks them up in each outcome GWAS and harmonises alleles;
   - runs MR: Wald ratio for one variant, inverse-variance weighted for more, plus Egger and weighted median from three variants;
   - runs heterogeneity and pleiotropy checks where possible.

   Outputs:
   - `results/mr_pilot_results.csv`
   - `results/mr_pilot_instruments.csv` (with F-statistics)
   - `results/mr_pilot_checks.csv`

3. **`mr/02_serpine1_followup.R`: the PAI-1 follow-up.** It looks up the instrument (rs2227631) in four other PAI-1 GWAS, including McCartney's methylation-estimated PAI-1, and runs a PheWAS of the variant (its other associations, p < 1e-5).

4. **`mr/03_coloc_serpine1.R`: colocalisation** of PAI-1 levels and parental longevity at SERPINE1 (±250 kb). PP.H4 above 0.8 supports one shared causal variant; a high PP.H3 means two different variants.

5. **The agent reads the results.** Steps 1–3 write `results/mr_pilot_exposures.csv`, `replication_rs2227631.csv` and `coloc_SERPINE1_parental_longevity.csv` next to the files above. `notebooks/target_ranking.ipynb` loads them all, and the agent reads them through a new tool, `get_causal_evidence` (`src/targetrank/causal.py`). Proteins without cis instruments are reported as *not tested*, not as null.

All API calls are cached in `mr/cache/` (git-ignored), so reruns are free and reproducible.

## Things to check when reading the results

- **Instrument strength:** F-statistic above 10 per variant.
- **Direction:** `b` is the effect of +1 unit of the protein (usually 1 SD) on the outcome. What a positive `b` means depends on how each GWAS was coded. **Check every new outcome with a variant of known effect.** For example, APOE ε4 (rs429358, allele C) shortens life and has a *positive* beta in the parental-longevity GWAS `ebi-a-GCST006697`, so there positive means shorter life. The script records this per outcome in `HARMFUL_SIGN` and writes the plain-language direction into the results.
- **One or two cis variants is normal for proteins.** Egger and weighted median then can't run, so colocalisation (next step) matters more.
- **pQTL platform:** a protein measured by SomaScan and by Olink can give different instruments. Replication across platforms strengthens a result.

## Pilot result (17 Nov 2026)

- **Five proteins had cis instruments; B2M and TIMP1 did not.** Both came from a small study of about 1,000 people.
- **Only PAI-1 (SERPINE1) showed a causal signal.** Genetically higher PAI-1 meant shorter parental lifespan: b = +0.070 per SD, p = 0.0015, Bonferroni-significant across 20 tests. The instrument was one promoter variant, rs2227631, F = 61. The direction matches the published Amish SERPINE1 loss-of-function finding.
- **ADM, cystatin C, GDF15 and leptin showed no effect** on parental longevity, frailty or GrimAge acceleration.

Follow-up of rs2227631 (step 2):

- **Allele G lowers PAI-1 in all three protein studies:** Pietzner (discovery), Gilly 2020 (−0.10, p = 0.012) and Sun 2018 (−0.04, p = 0.15).
- **It has no effect on methylation-estimated PAI-1,** GrimAge's surrogate (McCartney 2021: +0.06, p = 0.45, n = 34,448). The surrogate does not follow the genetics of the measured protein.
- **PheWAS (p < 1e-5):** lower SERPINE1 expression and lower tPA antigen (same pathway), expression of other nearby genes (a pleiotropy risk, tested by colocalisation), and small effects on pulse rate and red-cell count. No bleeding, lipid or BMI associations.
- **Data note:** OpenGWAS returns two different Pietzner effects for rs2227631 with the same SE: −0.103 (p = 6 × 10⁻¹⁵) from instrument extraction, the PheWAS and the region query, and −0.064 (p = 1 × 10⁻⁶) from a single-variant look-up. The dataset probably holds two rows for the variant. The MR used −0.103; either value gives a strong instrument (F = 61 or 24).

Colocalisation (step 3, ±250 kb, 2,290 variants):

- **PP.H4 = 0.13, PP.H3 = 0.04, PP.H1 = 0.83.** Inconclusive, not negative. PP.H1 dominates because the longevity GWAS has no strong signal in the region.
- **If there is a shared variant, it is the instrument:** rs2227631 carries 94% of the H4 probability.
- **The longevity GWAS's strongest variant in the window is rs4268055,** 70 kb upstream, with only p = 6 × 10⁻⁴ (rs2227631 itself: p = 0.0015). With an outcome signal this weak, coloc cannot reach PP.H4 > 0.8.
- **A ±1 Mb window gave PP.H3 = 0.19.** That came from a longevity signal (p = 4 × 10⁻⁵) outside the ±250 kb window, so it does not belong to SERPINE1.

Summary: the MR signal is Bonferroni-significant and replicates in direction across PAI-1 studies, but colocalisation is underpowered. A larger lifespan GWAS is needed to confirm it.

With these results, the agent changed its proposal for SERPINE1 from "unclear" to "inhibit" and lowered its scores for proteins with well-powered nulls. See part 3 of [WRITEUP.md](../WRITEUP.md).

## Next steps

1. The LD between rs4268055 and rs2227631 (`ieugwasr::ld_matrix`), and colocalisation against a larger lifespan GWAS (e.g. Timmers 2019).
2. Scale beyond the seven proteins: all proteins with cis instruments, then narrow to 50–200 with rules in code, before the agent.
