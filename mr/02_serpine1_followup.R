# Step 2: follow-up of the one significant result, PAI-1 (SERPINE1) -> shorter parental lifespan.
# Instrument: rs2227631, a promoter variant ~800 bp upstream of SERPINE1 (allele G lowers PAI-1).
#   a) Does the variant show the same direction in other PAI-1 studies, including the DNAm surrogate?
#   b) What else is the variant associated with? (pleiotropy, and an early look at on-target effects)

source("mr/R/setup.R")
load_token()

PROTEIN <- "SERPINE1"
SNP <- "rs2227631"

# a) Look-up in other PAI-1 GWAS, protein and methylation-estimated
PAI1_IDS <- c(pietzner2020_somascan = "ebi-a-GCST90019422",   # discovery
              sun2018_somascan      = "prot-a-2696",
              suhre2017_somascan    = "prot-c-2925_9_1",
              gilly2020             = "ebi-a-GCST90010245",
              dnam_pai1_mccartney   = "ebi-a-GCST90014291")   # GrimAge's methylation surrogate of PAI-1
lookup <- as.data.table(cached(paste0("lookup_", SNP, "_pai1"),
                               ieugwasr::associations(SNP, unname(PAI1_IDS), proxies = 1)))
lookup[, study := names(PAI1_IDS)[match(id, PAI1_IDS)]]
cols <- intersect(c("study", "id", "rsid", "ea", "nea", "eaf", "beta", "se", "p", "n"), names(lookup))
cat("\n== rs2227631 in PAI-1 studies (same direction = beta has the same sign for the same allele)\n")
print(lookup[, ..cols])
# Saved for the agent (src/agetarget/targets/causal.py), which puts every effect on the same allele
replication <- lookup[, ..cols]
replication[, `:=`(protein = PROTEIN,
                   measure = fifelse(study == "dnam_pai1_mccartney", "DNAm surrogate", "protein"))]
fwrite(replication, file.path(RESULTS_DIR, paste0("replication_", SNP, ".csv")))

# b) PheWAS: every OpenGWAS trait associated with the variant at p < 1e-5
phewas <- as.data.table(cached(paste0("phewas_", SNP), ieugwasr::phewas(SNP, pval = 1e-5)))
cols <- intersect(c("trait", "id", "ea", "nea", "beta", "p", "n"), names(phewas))
setorder(phewas, p)
cat("\n== PheWAS of", SNP, ":", nrow(phewas), "associations at p < 1e-5 (top 40)\n")
print(head(phewas[, ..cols], 40))
fwrite(phewas, file.path(RESULTS_DIR, paste0("phewas_", SNP, ".csv")))
cat("\nFull list: results/mr/phewas_", SNP, ".csv\n", sep = "")
