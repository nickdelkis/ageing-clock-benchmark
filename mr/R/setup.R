# Shared setup for the MR scripts: packages, project paths, OpenGWAS token, caching.
# Every script starts with:  source("mr/R/setup.R")  (working directory = project root)

suppressPackageStartupMessages({
  library(TwoSampleMR)
  library(ieugwasr)
  library(data.table)
  library(jsonlite)
})

PROJECT <- normalizePath(getwd())
CACHE_DIR <- file.path(PROJECT, "mr", "cache")
RESULTS_DIR <- file.path(PROJECT, "results")
dir.create(CACHE_DIR, showWarnings = FALSE, recursive = TRUE)
dir.create(RESULTS_DIR, showWarnings = FALSE, recursive = TRUE)
if (!file.exists(file.path(PROJECT, "docker-compose.yml"))) {
  stop("Run from the project root: in RStudio, Session > Set Working Directory > choose ~/work")
}

# RStudio sessions do not always see the container's environment variables,
# so fall back to reading the token straight from the project's .env file.
load_token <- function() {
  if (!nzchar(Sys.getenv("OPENGWAS_JWT"))) {
    env_file <- file.path(PROJECT, ".env")
    if (file.exists(env_file)) {
      hit <- grep("^\\s*OPENGWAS_JWT\\s*=", readLines(env_file, warn = FALSE), value = TRUE)
      if (length(hit)) {
        val <- trimws(sub("^\\s*OPENGWAS_JWT\\s*=", "", hit[1]))
        val <- gsub("^[\"']|[\"']$", "", val)
        if (nzchar(val)) Sys.setenv(OPENGWAS_JWT = val)
      }
    }
  }
  if (!nzchar(Sys.getenv("OPENGWAS_JWT"))) {
    stop("No OpenGWAS token. Add OPENGWAS_JWT=<token> to .env in the project folder (see mr/README.md).")
  }
  invisible(TRUE)
}

# Every API call goes through this: the first run downloads, later runs read mr/cache/.
# This saves OpenGWAS allowance and makes reruns reproducible.
cached <- function(key, expr) {
  path <- file.path(CACHE_DIR, paste0(gsub("[^A-Za-z0-9_.-]", "_", key), ".rds"))
  if (file.exists(path)) return(readRDS(path))
  value <- force(expr)
  saveRDS(value, path)
  value
}

# Gene coordinates on GRCh37, the build most OpenGWAS datasets use (check the `build` column).
# Only the coordinates are cached; the window is computed on each call, so `flank` always applies.
gene_region_grch37 <- function(symbol, flank = 1e6) {
  g <- cached(paste0("ensembl_grch37_", symbol), {
    j <- jsonlite::fromJSON(sprintf(
      "https://grch37.rest.ensembl.org/lookup/symbol/homo_sapiens/%s?content-type=application/json", symbol))
    list(chr = as.character(j$seq_region_name), start = j$start, end = j$end)
  })
  list(symbol = symbol, chr = g$chr, start = g$start, end = g$end,
       from = max(1, g$start - flank), to = g$end + flank)
}
