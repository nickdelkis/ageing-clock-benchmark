# Where ageing clocks disagree: one blood-methylation dataset

*Fill in after running the notebook. Aim for one page. Replace every [bracket].*

## Question

Published epigenetic clocks are often treated as interchangeable measures of "biological age". I ran [n] clocks on one public dataset to see where they agree, where they don't, and which of them register a condition associated with shorter life.

## Data and method

- **Dataset:** [GSE41169], whole blood, Illumina 450K, [n] samples aged [min–max] ([n_case] [condition], [n_control] controls).
- **Clocks:** [list], run with Biolearn [version]; [x]% of required CpGs imputed for [clock].
- **Age deviation:** residual of each clock regressed on chronological age.
- **Group test:** Cohen's d with 95% CI, Welch t-test, BH correction across clocks; repeated adjusting for sex.

## Findings

1. **Tracking age.** [Which clocks track age most closely, r and MAE; which are biased at the young/old ends. One sentence on why that is not the goal.]
2. **Agreement.** [Range of correlations between clocks' age deviations; which clocks cluster together; what that implies for using one clock as "the" biological age.]
3. **The condition.** [Which clocks show older age deviation in cases, effect sizes, whether it holds after sex adjustment. How this compares with large benchmarks (ComputAgeBench found second-generation clocks most robust).]

## Why they disagree

[Two or three sentences: training target (chronological age vs phenotype vs mortality vs longitudinal decline), odometer vs pace, and what blood DNA methylation can and cannot see.]

## Limitations

One dataset and small n; no cell-composition adjustment; [smoking/medication not available]; imputed CpGs; cross-sectional, so nothing about response to intervention.

## What I'd do next

[E.g. add cell-composition adjustment, run the same pipeline on a second cohort to check generalisability, or add a proteomic clock to compare data types.]
