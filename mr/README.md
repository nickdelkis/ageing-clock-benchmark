# Mendelian randomisation (part 3, in progress)

Goal: test whether genetically higher levels of each candidate protein *cause* faster epigenetic ageing or shorter lifespan. This uses public GWAS summary statistics only. The MR estimate gives the direction of effect (inhibit or activate), which the agent in part 2 often could not decide. The results will feed the agent as a new evidence tool.

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

All API calls are cached in `mr/cache/` (git-ignored), so reruns are free and reproducible.

## Things to check when reading the results

- **Instrument strength:** F-statistic above 10 per variant.
- **Direction:** `b` is the effect of +1 unit of the protein (usually 1 SD). For lifespan, b < 0 means harmful, so the hypothesis is to inhibit. For clock acceleration, b > 0 means harmful.
- **One or two cis variants is normal for proteins.** Egger and weighted median then can't run, so colocalisation (next step) matters more.
- **pQTL platform:** a protein measured by SomaScan and by Olink can give different instruments. Replication across platforms strengthens a result.

## Next steps (next session)

1. Run steps 0 and 1, then review the pilot results together.
2. Add a `get_causal_evidence` tool so the agent reads `mr_pilot_results.csv`.
3. Colocalisation (`coloc`) for the hits, using regional summary statistics.
4. Scale beyond the seven proteins: all proteins with cis instruments, then narrow to 50–200 with rules in code, before the agent.

The R scripts are a first draft written without an R environment to test in. Run them step by step and expect small fixes, for example to column names returned by the APIs.
