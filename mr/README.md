# Mendelian randomisation scripts

These scripts test whether genetically higher levels of each GrimAge protein shorten lifespan or speed up ageing, using public GWAS summary statistics. They write to `results/mr/`, where the agent reads them through its `get_causal_evidence` tool. Methods and results are in [docs/3-causal-direction.md](../docs/3-causal-direction.md).

They run in the `mr` container (R and RStudio Server) on the same project folder.

## One-time setup

1. **OpenGWAS token.** Sign in at <https://api.opengwas.io>, open your profile and generate a token. It is free; usage draws on an allowance that refills periodically. Add it to `.env` in the project folder:

   ```
   OPENGWAS_JWT=eyJ...
   ```

2. **Build the image** (once, roughly 10–20 minutes): `docker compose build mr`. The last build step prints `R packages OK`.

## Running

`docker compose up mr`, then open RStudio at <http://127.0.0.1:8787>. There is no login screen; it is reachable only from your own computer. Set the working directory to the project with *Session → Set Working Directory → Choose Directory → work*; every script expects it.

1. **`00_check_setup.R`** checks the token and writes two lookup tables to `results/mr/`: outcome GWAS candidates (lifespan, healthspan, frailty, epigenetic clocks) and pQTL datasets for the seven proteins. Pick one pQTL dataset per protein and the outcome ids, on build GRCh37.
2. **`01_cis_mr.R`** runs the MR, with the ids pasted into `EXPOSURE_IDS` and `OUTCOME_IDS` at the top. For each protein it takes clumped genome-wide significant variants within ±1 Mb of the gene, harmonises them with each outcome, and runs the Wald ratio or inverse-variance weighted estimate, Egger and weighted median from three variants, and heterogeneity checks. Writes `mr_results.csv`, `mr_exposures.csv`, `mr_instruments.csv` and `mr_checks.csv`.
3. **`02_serpine1_followup.R`** looks up the PAI-1 instrument (rs2227631) in four other PAI-1 GWAS, including GrimAge's methylation estimate of PAI-1, and runs a PheWAS of the variant. Writes `replication_rs2227631.csv` and `phewas_rs2227631.csv`.
4. **`03_coloc_serpine1.R`** colocalises PAI-1 levels and parental longevity within ±250 kb of SERPINE1. Writes a `coloc_*.csv` summary.

After a rerun, `python -m agetarget assess` rebuilds the target report, and a new agent batch (`python -m agetarget agent`) reads the new results.

All API calls are cached in `mr/cache/`, which is not committed, so reruns are free and reproducible.

## Things to check when reading the results

- **Instrument strength:** an F-statistic above 10 per variant.
- **Direction:** `b` is the effect of one unit of the protein, usually 1 SD, on the outcome, and what a positive `b` means depends on how each GWAS was coded. Check every new outcome with a variant of known effect: APOE ε4 (rs429358, allele C) shortens life and has a positive beta in the parental-longevity GWAS `ebi-a-GCST006697`, so there positive means shorter life. The script records this per outcome in `HARMFUL_SIGN` and writes the direction into the results.
- **One or two cis variants is normal for proteins.** Egger and weighted median then cannot run, so colocalisation matters more.
- **Platform:** the same protein measured by SomaScan and by Olink can give different instruments. Replication across platforms strengthens a result.
- **A data quirk:** OpenGWAS returns two different Pietzner effects for rs2227631 with the same SE: −0.103 (p = 6 × 10⁻¹⁵) from instrument extraction, the PheWAS and the region query, and −0.064 (p = 1 × 10⁻⁶) from a single-variant look-up. The MR used −0.103; either gives a strong instrument (F = 61 or 24). The exposure dataset is left out of the replication facts for this reason.
