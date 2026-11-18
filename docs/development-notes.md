# Development notes

How the project got to its current state: the versions of the agent's instructions, the failures along the way, and lessons that apply beyond this project.

## The agent's instructions, version by version

Every batch of agent runs is saved in `results/targets/agent_runs/` with full message traces. Earlier batches can be rebuilt without an LLM, for example `python -m agetarget assess --batch 20261116-215422`; v1 and v2 are rebuilt in `results/targets/rebuilt/`.

| Batch | Instructions | Runs per protein | Completed | Citations matching the evidence |
| --- | --- | --- | --- | --- |
| 20261116-214742 | v1, first test | 1 | 7 of 7 | 86 of 86 |
| 20261116-215422 | v1 | 3 | 21 of 21 | 254 of 254 |
| 20261116-223649 | v2 | 3 | 20 of 21 | 272 of 272 |
| 20261116-230637 | v2 | 3 | 21 of 21 | 286 of 286 |
| 20261117-094506 | v3, with MR | 3 | 21 of 21 | 264 of 265 |

### v1 → v2: what reading the reports found

Version 1 cited facts correctly. Reading its reports turned up four reasoning problems that the automated checks could not see:

| Version 1 problem | Version 2 change | Effect |
| --- | --- | --- |
| The rationale text was not checked, only the cited values | Every factual statement must come from a cited fact or be listed as the model's own knowledge | More claims are labelled as own knowledge |
| A clock-level finding (the GrimAge difference explained by smoking) was applied to B2M | The project context says exactly what each finding applies to, and the agent is told not to transfer findings | It states that it will not apply clock-level results to individual proteins |
| A conflict between sources went unnoticed (PAI-1: "advanced clinical" tractability against a phase 1 drug) | A required list of conflicts between sources, with which one was relied on | Up to three conflicts flagged per protein, including this one |
| An unclear recommendation ("worth considering to prioritise") | The recommendation must be stated in the summary's last sentence | Every summary ends with a clear recommendation |

Version 2 was more conservative and more consistent:

| Protein | v1 score | v2 score | v1 recommendations | v2 recommendations |
| --- | --- | --- | --- | --- |
| SERPINE1 | 3.50 | 3.37 | prioritise 2, consider 1 | consider 3 |
| ADM | 3.30 | 3.10 | consider 3 | consider 3 |
| GDF15 | 3.00 | 2.70 | consider 3 | consider 3 |
| CST3 | 2.88 | 2.85 | consider 2, deprioritise 1 | deprioritise 2, consider 1 |
| LEP | 2.30 | 2.30 | consider 2, deprioritise 1 | deprioritise 3 |

GDF15 dropped once its null finding in Shirai et al. was read correctly. The model and the database evidence were the same; only the instructions and the wording of the project context changed. The order of the top two was not fixed: in the single-run first test, ADM came first.

### v2 → v3: closing the gap the agent named

In 15 of its 21 version 2 assessments, covering every protein except leptin, the agent named Mendelian randomisation as the evidence that would decide the direction of modulation. Version 3 added that evidence as an eighth tool. What it changed is in [part 3](3-causal-direction.md).

## Failures worth knowing about

- **Silent truncation.** The stricter version 2 instructions made answers longer than the 2,048-token output limit. Truncated submissions arrived without their last fields and were rejected without the cause being stated. The model then dropped its largest field, the scores, to fit, and one assessment (SERPINE1, batch 20261116-223649) used all 14 of its turns without a valid submission. The fix:
  - raise the limit;
  - read the provider's stop reason and tell the model when its answer was cut off;
  - put the decision fields first in the format.

  A diagnostics table of rejections, nudges and repeated tool calls per run found the cause.
- **A citation checker that was too strict.** Early checks reported "mismatches" that were formatting differences, never wrong values: empty lists, quotes shortened with "...", lists cited as one string, JSON passed as text, UniProt reference tags removed from a quote. The checker now normalises formats but still rejects any value that is not in the evidence, and tests cover both directions.
- **Evidence drift.** Re-checking the version 1 runs the next day reported 18 failing citations. All were the project context: version 1 had quoted it correctly, but the settings now held the version 2 wording. Citations are now checked against the facts each run was shown, read back from its trace.
- **An impossible age.** A recorded age of 891 years in GSE80417 flattened every age regression in the cohort, and in a first run all six clocks showed cases as several years "older". Ages outside 0–110 are now treated as missing.

## Technical lessons

**Data**

- **GEO series matrices can be empty.** For GSE80417 and GSE84727 the betas are only in a supplementary file, indexed by Sentrix chip position. Biolearn's auto-scanned entries for them load metadata only.
- **Deposited data can be filtered.** GSE84727 lacks 65,000 probes, including all sex-chromosome probes. Check each model's CpG coverage before comparing cohorts.
- **Biolearn's default imputation fills only missing values of CpGs that are present.** An absent CpG makes the linear clocks fail and GrimAge2 silently compute without it. Use reference imputation (`sesame_450k`) when probe sets differ.
- **Biolearn has undeclared dependencies** (seaborn, torch), and pandas 3 breaks DunedinPACE, so pin `pandas<3`. Delete `.home/` after a pandas change: old pickle caches break.
- **Check which output column a model returns.** GrimAge2 once returned 250–350 years, because the wrapper took the first numeric column (a protein surrogate).

**APIs and LLMs**

- **Open Targets' GraphQL schema changes.** `drugAndClinicalCandidates` replaced `knownDrugs`, and stages are strings such as `PHASE_2_3`.
- **Some models reject a temperature setting,** so it is not sent by default.

**Mendelian randomisation**

- **Verify each outcome's sign with a variant of known effect** before reading a direction.
- **Cache keys must include every parameter.** A window bug once gave ±1 Mb instead of ±250 kb and inflated PP.H3.
- **OpenGWAS returned two different betas for the same variant** from different endpoints for one study, so the exposure dataset is excluded from the replication facts.
- **Report "not tested" separately from null.**

## Process

- **Keep the agent to judgement and do the rest in code.** Facts, checks, the baseline and the report are deterministic, so every claim can be audited.
- **Review output by reading it, not only through automated checks.** The v1 → v2 problems were found by reading reports.
- **Name the gap the agent cannot close, then close it with data.** Version 2 named MR; part 3 supplied it.
- **Check statements against saved outputs, not memory.** The rewrite of this repository recomputed every number in the write-up from the result files. Five statements in the earlier write-up did not survive, listed below.

## Corrections to earlier versions of the write-up

- **"The agent changed its proposal for PAI-1 from unclear to inhibit."** Wrong: PAI-1 was "inhibit" in every run of every version. MR moved the recommendation from consider to prioritise.
- **"With MR, PAI-1's ageing relevance and mechanism rose to 4."** Wrong: they were already 4 in version 2, and all five scores were unchanged.
- **"With MR, the baseline stopped agreeing on ageing relevance (ρ = 0.00)."** Wrong: ρ was already 0.00 in version 2. MR widened the absolute gap.
- **"Five of seven assessments named Mendelian randomisation."** An undercount: 15 of 21 assessments, covering six of the seven proteins.
- **"The clocks trained on chronological age are near zero in every cohort."** Not for GSE84727, where Hannum, PhenoAge and CausAge are modestly raised before blood-cell adjustment.
