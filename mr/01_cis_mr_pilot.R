# Step 1: cis-MR pilot for the seven GrimAge proteins.
# Question: do genetically higher levels of each protein cause faster epigenetic ageing or shorter lifespan?
# Output: results/mr_pilot_results.csv (one row per protein x outcome x method), read later by the agent.

source("mr/R/setup.R")
load_token()

# ---- Settings: fill in from the CSVs written by 00_check_setup.R --------------------
PROTEINS <- c("ADM", "B2M", "CST3", "SERPINE1", "GDF15", "LEP", "TIMP1")

# One OpenGWAS pQTL dataset id per protein (NA = skip). Prefer one study for all proteins, GRCh37 build.
EXPOSURE_IDS <- c(ADM = NA, B2M = NA, CST3 = NA, SERPINE1 = NA, GDF15 = NA, LEP = NA, TIMP1 = NA)

# Outcome dataset ids, named by what they measure, e.g. c(parental_lifespan = "...", grimage = "...")
OUTCOME_IDS <- c()

P_THRESHOLD <- 5e-8   # instrument p-value
CIS_FLANK   <- 1e6    # cis window: gene +/- 1 Mb
# ----------------------------------------------------------------------------------------

stopifnot("Fill in EXPOSURE_IDS and OUTCOME_IDS first" = any(!is.na(EXPOSURE_IDS)) && length(OUTCOME_IDS) > 0)

methods_for <- function(n) {
  if (n == 1) "mr_wald_ratio"
  else if (n == 2) "mr_ivw"
  else c("mr_ivw", "mr_egger_regression", "mr_weighted_median")
}

results <- list(); instruments <- list(); checks <- list()

for (protein in PROTEINS) {
  exp_id <- EXPOSURE_IDS[[protein]]
  if (is.na(exp_id)) next
  cat("\n==", protein, "(", exp_id, ")\n")

  # Genome-wide instruments, clumped by OpenGWAS, then restricted to the gene's cis window:
  # cis variants act on the protein itself, which makes the instrument far more credible.
  instr <- cached(paste0("instruments_", exp_id, "_p", P_THRESHOLD),
                  TwoSampleMR::extract_instruments(outcomes = exp_id, p1 = P_THRESHOLD, clump = TRUE))
  if (is.null(instr) || nrow(instr) == 0) { cat("   no instruments at p <", P_THRESHOLD, "\n"); next }
  reg <- gene_region_grch37(protein, flank = CIS_FLANK)
  cis <- subset(instr, as.character(chr.exposure) == reg$chr &
                       pos.exposure >= reg$from & pos.exposure <= reg$to)
  cat("  ", nrow(instr), "instruments genome-wide,", nrow(cis), "in the cis window\n")
  if (nrow(cis) == 0) next
  cis$exposure <- protein
  cis$F_stat <- (cis$beta.exposure / cis$se.exposure)^2   # > 10 is the usual 'strong instrument' rule
  instruments[[protein]] <- cis

  for (outcome_name in names(OUTCOME_IDS)) {
    out_id <- OUTCOME_IDS[[outcome_name]]
    out <- cached(paste0("outcome_", out_id, "_", protein),
                  TwoSampleMR::extract_outcome_data(snps = cis$SNP, outcomes = out_id, proxies = TRUE))
    if (is.null(out) || nrow(out) == 0) { cat("   ", outcome_name, ": instruments not found\n"); next }
    out$outcome <- outcome_name

    dat <- TwoSampleMR::harmonise_data(cis, out, action = 2)
    n <- sum(dat$mr_keep)
    if (n == 0) { cat("   ", outcome_name, ": nothing left after harmonisation\n"); next }

    res <- TwoSampleMR::mr(dat, method_list = methods_for(n))
    res$protein <- protein
    results[[paste(protein, outcome_name)]] <- res
    cat(sprintf("    %-20s n=%d  b=%.3f  p=%.2g\n", outcome_name, n, res$b[1], res$pval[1]))

    if (n >= 2) checks[[paste(protein, outcome_name, "het")]] <-
      cbind(protein = protein, TwoSampleMR::mr_heterogeneity(dat))
    if (n >= 3) checks[[paste(protein, outcome_name, "egger")]] <-
      cbind(protein = protein, TwoSampleMR::mr_pleiotropy_test(dat))
  }
}

res_all <- rbindlist(results, fill = TRUE)
fwrite(res_all, file.path(RESULTS_DIR, "mr_pilot_results.csv"))
fwrite(rbindlist(instruments, fill = TRUE), file.path(RESULTS_DIR, "mr_pilot_instruments.csv"))
if (length(checks)) fwrite(rbindlist(checks, fill = TRUE), file.path(RESULTS_DIR, "mr_pilot_checks.csv"))

cat("\nWrote results/mr_pilot_results.csv,", nrow(res_all), "rows.\n",
    "Reading b: effect of +1 unit (usually SD) of the protein on the outcome.",
    "For lifespan, b < 0 means harmful (hypothesis: inhibit); for clock acceleration, b > 0 means harmful.\n")
