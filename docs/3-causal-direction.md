# 3. Causal direction: Mendelian randomisation of the GrimAge proteins

## Summary

Without causal evidence, the agent of [part 2](2-target-triage.md) could rarely say whether a protein should be inhibited or activated. In 15 of its 21 assessments, covering every protein except leptin, it named Mendelian randomisation (MR) as the evidence that would decide it. This part runs that analysis on public summary statistics and gives the results to the agent as an eighth evidence tool.

- **Five of the seven proteins could be tested. One result survived correction for 20 tests:** genetically higher PAI-1 (SERPINE1) was associated with shorter parental lifespan (p = 0.0015, Bonferroni p = 0.03). This matches Amish carriers of a SERPINE1 loss-of-function variant, who live longer.
- **The instrument's direction replicated in two other PAI-1 studies,** but not in GrimAge's methylation estimate of PAI-1. Colocalisation was inconclusive, because the lifespan GWAS has only a weak signal at the locus.
- **In the agent,** the MR result gave causal support to a direction it had already proposed for PAI-1 from its biology, inhibit, and moved its recommendation from consider (3 of 3 runs) to prioritise (2 of 3). Well-powered null results lowered the scores of cystatin C and leptin.

## Design

Two-sample cis-MR: variants near a protein's own gene that change its plasma level act as a natural experiment in raising or lowering the protein. Everything runs in R (TwoSampleMR, ieugwasr, coloc) on GWAS summary statistics hosted by OpenGWAS. Every API call is cached, so reruns are free and reproducible.

**Exposures,** one protein GWAS each:

| Protein | Study | Platform | n | Cis instruments |
| --- | --- | --- | --- | --- |
| ADM | Folkersen 2020 | Olink | 21,758 | 2 |
| B2M | Suhre 2017 | SomaScan | about 1,000 | 0 |
| CST3 (cystatin C) | UK Biobank serum biochemistry | clinical assay | 437,846 | 6 |
| SERPINE1 (PAI-1) | Pietzner 2020 | SomaScan | 10,708 | 1 |
| GDF15 | Folkersen 2020 | Olink | 21,758 | 2 |
| LEP (leptin) | Folkersen 2020 | Olink | 21,758 | 1 |
| TIMP1 | Suhre 2017 | SomaScan | about 1,000 | 0 |

**Outcomes:**

- parental lifespan: Pilling 2017, 389,166 UK Biobank participants;
- frailty index: Atkins 2021, 175,226 people;
- GrimAge acceleration: McCartney 2021, 34,467 people, two entries in OpenGWAS.

**Method:**

- **Instruments:** p < 5 × 10⁻⁸, clumped, within 1 Mb of the protein's gene. Restricting to cis variants makes it more likely that a variant acts through the protein itself.
- **Estimators:** Wald ratio for one variant, inverse-variance weighted for more. Egger and weighted median from three variants; heterogeneity tested from two.
- **Multiple testing:** Bonferroni over the 20 primary tests (5 proteins × 4 outcomes).
- **Direction check:** what a positive beta means depends on how each GWAS was coded. Each outcome was checked against a variant of known effect: APOE ε4 (rs429358) has a positive beta in the parental-lifespan GWAS, so there positive means shorter life.

## Results

### Only PAI-1 showed a causal signal

| Protein | Variants | Effect on parental lifespan | p |
| --- | --- | --- | --- |
| SERPINE1 | 1 | shorter (b = +0.070) | 0.0015 (Bonferroni 0.03) |
| LEP | 1 | b = +0.045 | 0.14 |
| ADM | 2 | b = +0.015 | 0.30 |
| GDF15 | 2 | b = +0.009 | 0.69 |
| CST3 | 6 | b = −0.001 | 0.82 |

No other test of any protein on frailty or GrimAge acceleration reached p < 0.1. B2M and TIMP1 could not be tested: their only pQTL source here has about 1,000 people and gave no cis instruments. The PAI-1 direction matches the Amish carriers of a loss-of-function SERPINE1 variant, who live longer than non-carriers (Khan et al. 2017).

### Follow-up of the PAI-1 instrument

The instrument is rs2227631, a promoter variant about 1 kb upstream of SERPINE1, with F = 61. Its G allele lowers PAI-1.

- **Replication across protein studies.** The G allele lowered PAI-1 in Gilly 2020 (β = −0.10, p = 0.012) and, non-significantly, in Sun 2018 (β = −0.04, p = 0.15).
- **No effect on GrimAge's methylation estimate of PAI-1** (McCartney 2021: β = +0.06, p = 0.45, n = 34,448). The surrogate does not follow the genetics of the measured protein. Together with part 1, where GrimAge's signal tracked smoking, this says the clock's protein components are proxies for exposure, not for the proteins themselves.
- **PheWAS** (p < 10⁻⁵, 9 associations): PAI-1 itself; tissue plasminogen activator, in the same pathway; expression of SERPINE1 and four other genes; small effects on pulse rate and red-cell count. There were no associations with bleeding, lipids or BMI.

### Colocalisation is inconclusive

Colocalisation tests whether one shared variant drives both the PAI-1 and the lifespan signal (H4), or two different variants in linkage disequilibrium do (H3). Within ±250 kb of SERPINE1 (2,290 variants):

| H0 no signal | H1 PAI-1 only | H2 lifespan only | H3 two variants | H4 one shared variant |
| --- | --- | --- | --- | --- |
| 0.00 | 0.83 | 0.00 | 0.04 | 0.13 |

- **If there is a shared variant, it is the instrument:** rs2227631 carries 94% of the H4 probability.
- **The lifespan GWAS has no strong signal at this locus.** Its strongest variant in the window, rs4268055 (70 kb upstream), reaches only p = 6 × 10⁻⁴. A signal this weak cannot push PP.H4 towards the usual 0.8.
- **The window matters.** A ±1 Mb window first gave PP.H3 = 0.19, from a lifespan signal outside the ±250 kb window that does not belong to SERPINE1.

The MR result is Bonferroni-significant and directionally replicated; colocalisation is underpowered, not contradictory.

### GDF15: a null hiding a disagreement

GDF15's two cis variants disagree with each other on three of the four outcomes (heterogeneity Q p = 0.008 for parental lifespan, 0.001 for both GrimAge entries). Its null estimate averages variants pulling in different directions; it is not two variants agreeing on no effect. One possibility is an assay artefact: a protein-altering variant can change antibody binding in an immunoassay without changing the protein level.

## What the MR evidence changed in the agent

The results became an eighth tool, `get_causal_evidence`, returning short, citable facts per protein: instruments and F-statistics, the estimate per outcome with Bonferroni p, a direction only when significant, heterogeneity, colocalisation, replication and the top PheWAS traits. Proteins without instruments are reported as "not tested", not as null. The instructions gained one rule: a significant MR result is the strongest available evidence for ageing relevance and direction, weighed with colocalisation; a null is weak evidence against; "not tested" is no evidence either way.

Same model and evidence otherwise, three runs per protein, without (version 2) and with (version 3) the MR tool:

| Protein | Score v2 → v3 | Recommendations v2 | Recommendations v3 | Modulation, both versions |
| --- | --- | --- | --- | --- |
| SERPINE1 | 3.37 → 3.37 | consider 3 | prioritise 2, consider 1 | inhibit |
| ADM | 3.10 → 3.20 | consider 3 | consider 3 | unclear |
| GDF15 | 2.70 → 2.70 | consider 3 | consider 3 | unclear |
| B2M | 2.70 → 2.58 | consider 3 | consider 3 | unclear |
| TIMP1 | 2.50 → 2.30 | deprioritise 2, consider 1 | deprioritise 2, consider 1 | unclear |
| CST3 | 2.85 → 2.25 | deprioritise 2, consider 1 | deprioritise 3 | unclear |
| LEP | 2.30 → 1.95 | deprioritise 3 | deprioritise 3 | unclear |

- **For PAI-1, MR changed the strength of the case, not its content.** All five scores and the direction were the same in both versions. Without MR the agent reasoned from biology: "reducing its activity is the likely direction for ageing, but the causal link between PAI-1 and ageing in humans is less well defined". With MR: "MR points to inhibition, but this rests on one instrument without sensitivity checks". The recommendation moved from consider to prioritise in two of three runs. Safety stayed low because inhibiting PAI-1 carries a bleeding risk.
- **Well-powered nulls were penalised.** Cystatin C's ageing relevance fell from 3.7 to 2.0: six instruments from 438,000 people found nothing. Leptin's fell from 3.0 to 2.0, on a null from a single variant.
- **Untested proteins were not penalised for missing data.** The ageing relevance of B2M and TIMP1 did not change; they listed the missing MR among their key uncertainties. TIMP1's lower overall score comes from its safety score, not from MR.
- **The gap with the rule-based baseline widened on ageing relevance** (mean absolute difference 1.05 → 1.43), because the baseline does not read MR. Their rank agreement on that dimension was already zero in version 2.
- **Citations: 264 of 265 matched** (see part 2).

## Limitations

- **One variant for PAI-1.** A single instrument cannot separate an effect through PAI-1 from pleiotropy at the locus; the PheWAS found expression effects on four other genes.
- **Colocalisation is underpowered,** so it neither confirms nor refutes the shared variant.
- **Parental lifespan is a proxy.** It measures the participants' parents and dilutes effects. GrimAge acceleration (n = 34,467) has far less power than lifespan (n = 389,166), so its null says little.
- **One pQTL platform per protein.** SomaScan and Olink can give different instruments for the same protein; the PAI-1 result has not been tested with Olink instruments.
- **Small or indirect sources for some proteins.** B2M and TIMP1 relied on a study of about 1,000 people, and CST3 on a clinical assay of cystatin C, which also reflects kidney function.

## Next

- **Test PAI-1 with Olink instruments,** for example from the UK Biobank Pharma Proteomics Project, and colocalise against a larger lifespan GWAS: Timmers 2019 (one million parent lifespans) or the multivariate healthspan–lifespan–longevity scan (Timmers 2020).
- **Check the LD between rs4268055 and rs2227631,** and whether either GDF15 instrument is a missense variant.
- **Scale up:** cis-MR for every protein with instruments, before the agent (see part 2).

## References

- Pilling LC, et al. (2017) Human longevity: 25 genetic loci associated in 389,166 UK biobank participants. *Aging*. [doi:10.18632/aging.101334](https://doi.org/10.18632/aging.101334)
- Atkins JL, et al. (2021) A genome-wide association study of the frailty index highlights brain pathways in ageing. *Aging Cell*. [doi:10.1111/acel.13459](https://doi.org/10.1111/acel.13459)
- McCartney DL, et al. (2021) Genome-wide association studies identify 137 genetic loci for DNA methylation biomarkers of aging. *Genome Biology* 22:194. [doi:10.1186/s13059-021-02398-9](https://doi.org/10.1186/s13059-021-02398-9)
- Pietzner M, et al. (2020) Genetic architecture of host proteins involved in SARS-CoV-2 infection. *Nature Communications*. [doi:10.1038/s41467-020-19996-z](https://doi.org/10.1038/s41467-020-19996-z)
- Folkersen L, et al. (2020) Genomic and drug target evaluation of 90 cardiovascular proteins in 30,931 individuals. *Nature Metabolism*. [doi:10.1038/s42255-020-00287-2](https://doi.org/10.1038/s42255-020-00287-2)
- Suhre K, et al. (2017) Connecting genetic risk to disease end points through the human blood plasma proteome. *Nature Communications*. [doi:10.1038/ncomms14357](https://doi.org/10.1038/ncomms14357)
- Sun BB, et al. (2018) Genomic atlas of the human plasma proteome. *Nature*. [doi:10.1038/s41586-018-0175-2](https://doi.org/10.1038/s41586-018-0175-2)
- Gilly A, et al. (2020) Whole-genome sequencing analysis of the cardiometabolic proteome. *Nature Communications*. [doi:10.1038/s41467-020-20079-2](https://doi.org/10.1038/s41467-020-20079-2)
- Khan SS, et al. (2017) A null mutation in SERPINE1 protects against biological aging in humans. *Science Advances*. [doi:10.1126/sciadv.aao1617](https://doi.org/10.1126/sciadv.aao1617)
- Giambartolomei C, et al. (2014) Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*. [doi:10.1371/journal.pgen.1004383](https://doi.org/10.1371/journal.pgen.1004383)
- Hemani G, et al. (2018) The MR-Base platform supports systematic causal inference across the human phenome. *eLife*. [doi:10.7554/eLife.34408](https://doi.org/10.7554/eLife.34408)
- Timmers PR, et al. (2019) Genomics of 1 million parent lifespans implicates novel pathways and common diseases and distinguishes survival chances. *eLife*. [doi:10.7554/eLife.39856](https://doi.org/10.7554/eLife.39856)
- Timmers PR, et al. (2020) Multivariate genomic scan implicates novel loci and haem metabolism in human ageing. *Nature Communications*. [doi:10.1038/s41467-020-17312-3](https://doi.org/10.1038/s41467-020-17312-3)
