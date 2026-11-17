# Step 3: colocalisation at SERPINE1 between PAI-1 levels and parental longevity.
# Question: is one shared causal variant behind both signals (supports the MR result), or two
# different variants in linkage disequilibrium (the MR result would then be confounded by LD)?
# coloc reports five posterior probabilities:
#   H0 no signal; H1 PAI-1 only; H2 longevity only; H3 both, different variants; H4 both, shared variant.
# Rule of thumb: PP.H4 > 0.8 supports colocalisation; high PP.H3 argues against.

source("mr/R/setup.R")
load_token()
suppressPackageStartupMessages(library(coloc))

PROTEIN     <- "SERPINE1"
OUTCOME     <- "parental_longevity"   # name as in 01_cis_mr_pilot.R
EXPOSURE_ID <- "ebi-a-GCST90019422"   # PAI-1, Pietzner 2020 (SomaScan)
OUTCOME_ID  <- "ebi-a-GCST006697"     # parental longevity, Pilling 2017
N_EXP <- 10708
N_OUT <- 389166
FLANK <- 250000                        # +/- 250 kb around SERPINE1 (keeps the API query small)

reg <- gene_region_grch37(PROTEIN, flank = FLANK)
region <- sprintf("%s:%d-%d", reg$chr, reg$from, reg$to)
get_region <- function(id) as.data.table(cached(paste0("region_", id, "_", gsub("[:-]", "_", region)),
                                                ieugwasr::associations(region, id, proxies = 0)))

prep <- function(d) {
  d <- d[!is.na(beta) & !is.na(se) & se > 0]
  setorder(d, p)
  d <- d[!duplicated(rsid)]          # some datasets hold duplicate rows per variant: keep the strongest
  d[, .(snp = rsid, position, beta, varbeta = se^2, eaf)]
}
e <- prep(get_region(EXPOSURE_ID))
o <- prep(get_region(OUTCOME_ID))

common <- intersect(e$snp, o$snp)
e <- e[snp %in% common][order(snp)]
o <- o[snp %in% common][order(snp)]
cat(length(common), "variants in both datasets in", region, "\n")

# Minor allele frequency: from each dataset, falling back to the exposure if the outcome lacks it
maf <- function(eaf) pmin(eaf, 1 - eaf)
e[, MAF := maf(eaf)]
o[, MAF := fifelse(is.na(eaf), e$MAF, maf(eaf))]
keep <- !is.na(e$MAF) & e$MAF > 0 & !is.na(o$MAF) & o$MAF > 0
e <- e[keep]; o <- o[keep]

d1 <- list(snp = e$snp, position = e$position, beta = e$beta, varbeta = e$varbeta,
           MAF = e$MAF, N = N_EXP, type = "quant")
d2 <- list(snp = o$snp, position = o$position, beta = o$beta, varbeta = o$varbeta,
           MAF = o$MAF, N = N_OUT, type = "quant")

res <- coloc::coloc.abf(d1, d2)        # default priors: p1 = p2 = 1e-4, p12 = 1e-5

cat("\n== Posterior probabilities\n")
print(round(res$summary, 3))
cat("\n== Strongest variant per trait in the region (distance from the gene start)\n")
tops <- list()
for (nm in c("exposure", "outcome")) {
  d <- if (nm == "exposure") e else o
  top <- d[which.max(abs(beta) / sqrt(varbeta))]
  z <- top$beta / sqrt(top$varbeta)
  tops[[nm]] <- list(snp = top$snp, kb = (top$position - reg$start) / 1000, z = z, p = 2 * pnorm(-abs(z)))
  cat(sprintf("  %-10s %s  pos %d (%+.0f kb)  z = %.1f\n", nm, top$snp, top$position, tops[[nm]]$kb, z))
}

cat("\n== Variants most likely to be the shared causal variant (if H4)\n")
print(head(as.data.table(res$results)[order(-SNP.PP.H4), .(snp, SNP.PP.H4 = round(SNP.PP.H4, 3))], 5))

# Optional: how PP.H4 depends on the prior for a shared variant (draws a plot in RStudio)
# coloc::sensitivity(res, rule = "H4 > 0.5")

top_h4 <- as.data.table(res$results)[which.max(SNP.PP.H4)]
# One summary row, read by the agent's get_causal_evidence tool (src/targetrank/causal.py)
summary_row <- cbind(
  data.table(protein = PROTEIN, outcome = OUTCOME, exposure_id = EXPOSURE_ID, outcome_id = OUTCOME_ID,
             region = region, flank_kb = FLANK / 1000),
  as.data.table(as.list(res$summary)),
  data.table(top_snp = top_h4$snp, top_snp_pp_h4 = top_h4$SNP.PP.H4,
             outcome_top_snp = tops$outcome$snp, outcome_top_kb = tops$outcome$kb,
             outcome_min_p = tops$outcome$p, exposure_top_snp = tops$exposure$snp))
out_file <- file.path(RESULTS_DIR, sprintf("coloc_%s_%s.csv", PROTEIN, OUTCOME))
fwrite(summary_row, out_file)
cat("\nSaved", sub(paste0(PROJECT, "/"), "", out_file, fixed = TRUE), "\n")
