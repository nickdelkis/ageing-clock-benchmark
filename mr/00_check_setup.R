# Step 0: check the setup and find which OpenGWAS datasets to use.
# Run once, top to bottom. Nothing here is analysis; it writes two lookup tables to results/mr/.

source("mr/R/setup.R")

# 1. Token works?
load_token()
print(ieugwasr::user())            # your OpenGWAS account; errors here mean the token is wrong or expired

# 2. All OpenGWAS datasets (one call, cached)
info <- as.data.table(cached("gwasinfo_all", ieugwasr::gwasinfo()))
cat(nrow(info), "datasets in OpenGWAS\n")
keep_cols <- intersect(c("id", "trait", "author", "year", "consortium", "population", "sample_size",
                         "nsnp", "build", "pmid"), names(info))

# 3. Candidate OUTCOME datasets: lifespan, healthspan, frailty, epigenetic clocks
outcome_pattern <- "lifespan|longevity|healthspan|frailty|grimage|phenoage|hannum|horvath|epigenetic age|age acceleration"
outcomes <- info[grepl(outcome_pattern, trait, ignore.case = TRUE, perl = TRUE), ..keep_cols]
if ("sample_size" %in% names(outcomes)) setorder(outcomes, -sample_size)
fwrite(outcomes, file.path(RESULTS_DIR, "opengwas_outcome_candidates.csv"))
cat("\nOutcome candidates:", nrow(outcomes), "-> results/mr/opengwas_outcome_candidates.csv\n")
print(head(outcomes[, intersect(c("id", "trait", "author", "year", "sample_size", "build"), keep_cols), with = FALSE], 25))

# 4. Candidate EXPOSURE datasets: pQTL studies for the seven GrimAge proteins
protein_pattern <- paste(c("adrenomedullin", "\\bADM\\b", "beta-2-microglobulin", "\\bB2M\\b", "cystatin",
                           "\\bCST3\\b", "plasminogen activator inhibitor", "\\bPAI-?1\\b", "SERPINE1",
                           "GDF15", "GDF-15", "growth differentiation factor 15", "leptin", "\\bLEP\\b",
                           "TIMP-?1", "metalloproteinase inhibitor 1"), collapse = "|")
exposures <- info[grepl(protein_pattern, trait, ignore.case = TRUE, perl = TRUE), ..keep_cols]
fwrite(exposures, file.path(RESULTS_DIR, "opengwas_pqtl_candidates.csv"))
cat("\npQTL candidates:", nrow(exposures), "-> results/mr/opengwas_pqtl_candidates.csv\n")
print(exposures[, intersect(c("id", "trait", "author", "year", "sample_size", "build"), keep_cols), with = FALSE])

# 5. Which pQTL collections exist? (look for batch ids starting with "prot-")
batches <- as.data.table(cached("batches", ieugwasr::batches()))
print(batches[apply(batches, 1, function(r) any(grepl("prot", r, ignore.case = TRUE)))])

cat("\nNext: open the two CSVs, pick one pQTL id per protein and the outcome ids,",
    "\nand paste them into the settings at the top of mr/01_cis_mr.R\n")
