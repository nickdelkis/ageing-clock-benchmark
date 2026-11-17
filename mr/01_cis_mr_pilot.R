# Step 1: cis-MR pilot for the seven GrimAge proteins.
# Question: do genetically higher levels of each protein cause faster epigenetic ageing or shorter lifespan?
# Output: results/mr_pilot_*.csv, read by the agent's get_causal_evidence tool (src/targetrank/causal.py).

source("mr/R/setup.R")
load_token()

# ---- Settings: fill in from the CSVs written by 00_check_setup.R --------------------
PROTEINS <- c("ADM", "B2M", "CST3", "SERPINE1", "GDF15", "LEP", "TIMP1")

# One OpenGWAS pQTL dataset id per protein (NA = skip). Prefer one study for all proteins, GRCh37 build.
EXPOSURE_IDS <- c(ADM      = "ebi-a-GCST90011996",   # SCALLOP, Olink, n = 21,758
                  B2M      = "prot-c-3485_28_2",     # Suhre 2017, SomaScan, ~1,000
                  CST3     = "ebi-a-GCST90025945",   # UK Biobank serum cystatin C, n = 437,846
                  SERPINE1 = "ebi-a-GCST90019422",   # Pietzner 2020, SomaScan, n = 10,708
                  GDF15    = "ebi-a-GCST90011998",   # SCALLOP, Olink, n = 21,758
                  LEP      = "ebi-a-GCST90012076",   # SCALLOP, Olink, n = 21,758
                  TIMP1    = "prot-c-2211_9_6")      # Suhre 2017, SomaScan, ~1,000

# Outcome dataset ids, named by what they measure
OUTCOME_IDS <- c(parental_longevity = "ebi-a-GCST006697",   # Pilling 2017, n = 389,166
                 frailty            = "ebi-a-GCST90020053", # Atkins 2021, n = 175,226
                 grimage_accel_a    = "ebi-a-GCST90014288", # McCartney 2021, n = 34,467 (primary)
                 grimage_accel_b    = "ebi-a-GCST90014300") # same study, second entry

# Sign of a beta that means WORSE ageing, per outcome. Check new outcomes with a known variant:
# APOE e4 (rs429358, allele C) has beta +0.057 in ebi-a-GCST006697, so positive = shorter parental life.
HARMFUL_SIGN <- c(parental_longevity = +1, frailty = +1, grimage_accel_a = +1, grimage_accel_b = +1)

P_THRESHOLD <- 5e-8   # instrument p-value
CIS_FLANK   <- 1e6    # cis window: gene +/- 1 Mb
# ----------------------------------------------------------------------------------------

stopifnot("Fill in EXPOSURE_IDS and OUTCOME_IDS first" = any(!is.na(EXPOSURE_IDS)) && length(OUTCOME_IDS) > 0,
          "Give a HARMFUL_SIGN for every outcome" = all(names(OUTCOME_IDS) %in% names(HARMFUL_SIGN)))

methods_for <- function(n) {
  if (n == 1) "mr_wald_ratio"
  else if (n == 2) "mr_ivw"
  else c("mr_ivw", "mr_egger_regression", "mr_weighted_median")
}

# "Author year (id, n = ...)" for a dataset, from OpenGWAS metadata
study_label <- function(id) {
  g <- cached(paste0("gwasinfo_", id), ieugwasr::gwasinfo(id))
  field <- function(x) if (!is.null(g) && x %in% names(g) && !is.na(g[[x]][1])) as.character(g[[x]][1]) else NA
  n <- suppressWarnings(as.numeric(field("sample_size")))
  sprintf("%s (%s%s)", paste(na.omit(c(field("author"), field("year"))), collapse = " "), id,
          if (is.na(n)) "" else paste0(", n = ", format(n, big.mark = ",")))
}

results <- list(); instruments <- list(); checks <- list(); exposures <- list()
exposure_row <- function(protein, exp_id, n_gw, n_cis)
  data.table(protein = protein, exposure_id = exp_id, study = if (is.na(exp_id)) NA else study_label(exp_id),
             n_genome_wide = n_gw, n_cis = n_cis)

for (protein in PROTEINS) {
  exp_id <- EXPOSURE_IDS[[protein]]
  if (is.na(exp_id)) { exposures[[protein]] <- exposure_row(protein, NA, 0, 0); next }
  cat("\n==", protein, "(", exp_id, ")\n")

  # Genome-wide instruments, clumped by OpenGWAS, then restricted to the gene's cis window:
  # cis variants act on the protein itself, which makes the instrument far more credible.
  instr <- cached(paste0("instruments_", exp_id, "_p", P_THRESHOLD),
                  TwoSampleMR::extract_instruments(outcomes = exp_id, p1 = P_THRESHOLD, clump = TRUE))
  if (is.null(instr) || nrow(instr) == 0) {
    cat("   no instruments at p <", P_THRESHOLD, "\n")
    exposures[[protein]] <- exposure_row(protein, exp_id, 0, 0)
    next
  }
  reg <- gene_region_grch37(protein, flank = CIS_FLANK)
  cis <- subset(instr, as.character(chr.exposure) == reg$chr &
                       pos.exposure >= reg$from & pos.exposure <= reg$to)
  cat("  ", nrow(instr), "instruments genome-wide,", nrow(cis), "in the cis window\n")
  exposures[[protein]] <- exposure_row(protein, exp_id, nrow(instr), nrow(cis))
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

# Plain-language direction, and a Bonferroni correction over the primary estimate of each pair
res_all[, harmful_sign := HARMFUL_SIGN[outcome]]
res_all[, direction := fifelse(sign(b) * harmful_sign > 0,
                               "higher protein -> worse ageing (hypothesis: inhibit)",
                               "higher protein -> better ageing (hypothesis: activate)")]
res_all[, primary := method %in% c("Wald ratio", "Inverse variance weighted")]
n_tests <- res_all[primary == TRUE, .N]
res_all[primary == TRUE, p_bonferroni := pmin(1, pval * n_tests)]

fwrite(res_all, file.path(RESULTS_DIR, "mr_pilot_results.csv"))
fwrite(rbindlist(exposures), file.path(RESULTS_DIR, "mr_pilot_exposures.csv"))
fwrite(rbindlist(instruments, fill = TRUE), file.path(RESULTS_DIR, "mr_pilot_instruments.csv"))
if (length(checks)) fwrite(rbindlist(checks, fill = TRUE), file.path(RESULTS_DIR, "mr_pilot_checks.csv"))

cat("\nWrote results/mr_pilot_results.csv:", nrow(res_all), "rows,", n_tests, "primary tests.\n")
print(res_all[primary == TRUE][order(pval), .(protein, outcome, method, nsnp, b = round(b, 3),
                                              pval = signif(pval, 2), p_bonferroni = signif(p_bonferroni, 2), direction)])
