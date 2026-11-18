# Target assessment report

Candidate targets: the seven GrimAge proteins. Evidence retrieved 2026-11-16.

Model: `anthropic:claude-sonnet-5-5 @ https://api.anthropic.com`. Runs per target: 3.

Citation check: 264 of 265 cited facts match the evidence exactly, 0 are close paraphrases of a text fact, 1 do not match, and 0 cite facts that do not exist (checked against the evidence the agent was shown in each run).

| Rank | Target | Agent score (range) | Baseline | Recommendations across runs |
| --- | --- | --- | --- | --- |
| 1 | SERPINE1 | 3.37 (3.30-3.50) | 3.50 | prioritise 2, consider 1 |
| 2 | ADM | 3.20 (3.05-3.35) | 4.00 | consider 3 |
| 3 | GDF15 | 2.70 (2.70-2.70) | 3.45 | consider 3 |
| 4 | B2M | 2.58 (2.35-2.70) | 2.30 | consider 3 |
| 5 | TIMP1 | 2.30 (2.30-2.30) | 2.95 | deprioritise 2, consider 1 |
| 6 | CST3 | 2.25 (2.25-2.25) | 3.35 | deprioritise 3 |
| 7 | LEP | 1.95 (1.85-2.00) | 2.95 | deprioritise 3 |

## SERPINE1

Representative run 1 (median score). **Recommendation:** prioritise. **Proposed modulation:** inhibit.

SERPINE1 (PAI-1) is a secreted inhibitor of tPA and uPA that is involved in senescence. Genetically higher PAI-1 is associated with worse parental longevity (Bonferroni-significant, one cis instrument). Colocalisation is inconclusive and the frailty and GrimAge outcomes are null. It is tractable for small molecules and antibodies, but only a phase 1 drug is listed, and bleeding and osteonecrosis liabilities are a concern. The ageing evidence is multi-source and the direction (inhibit) is consistent, so I recommend prioritise, with attention to bleeding safety.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | Genetically higher PAI-1 is linked to worse parental longevity (Bonferroni-significant), and about 21% of papers concern ageing. It is associated with several age-related diseases. Colocalisation is inconclusive and the other MR outcomes are null, which tempers the score. |
| mechanism | 4 | PAI-1 is a well-characterised inhibitor of tPA and uPA that regulates fibrinolysis and is implicated in cellular senescence. MR points to inhibition, but this rests on one instrument without sensitivity checks. |
| tractability | 4 | Small-molecule evidence is strong (clinical-stage, ligand-bound structure, high-quality pocket). It is also a secreted protein, so an antibody is feasible. No approved drug is shown. |
| safety | 2 | Open Targets lists two liabilities, including osteonecrosis. Congenital PAI-1 deficiency is associated with abnormal bleeding and haemorrhage, so inhibition carries a bleeding risk. |
| clinical precedence | 2 | Only one drug, aleplasinin, is listed, and it reached phase 1. |

**Key uncertainties:**

- Colocalisation for parental longevity is inconclusive (PP.H4 0.13, PP.H1 0.83), so the MR signal may not share a causal variant with the protein
- Only one cis instrument, so pleiotropy cannot be tested
- Frailty and GrimAge MR are null
- Bleeding risk of chronic PAI-1 inhibition in older people
- Replication of the instrument is mixed (Gilly p = 0.012, Sun p = 0.15)

**Conflicts between sources:**

- Small-molecule tractability is labelled 'Advanced Clinical', but the clinical candidates list shows only a phase 1 drug (aleplasinin). I relied on the clinical candidates list for clinical precedence.
- The MR effect on parental longevity is Bonferroni-significant, but colocalisation is inconclusive (PP.H4 0.13) and the frailty and GrimAge MR are null. I treated the MR as supportive but not conclusive.

**Claims from model knowledge, not from the evidence tools:**

- Inhibiting an inhibitor of fibrinolysis would plausibly raise bleeding risk, particularly alongside anticoagulants

## ADM

Representative run 0 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

ADM is a secreted vasodilatory peptide with cardiovascular disease associations. About 18% of its literature concerns ageing. MR of the measured protein, using two cis variants, shows no significant effect on frailty, parental longevity or GrimAge acceleration. Tractability is good, since an antibody (enibarcimab) has reached Phase 2/3, and no safety liabilities are listed. The direction of modulation is unclear, and ADM may be protective in the cardiovascular system. Recommendation: consider.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About 18% of ADM papers concern ageing, and it is linked to cardiovascular age-related diseases. MR of the measured protein is null on all four ageing outcomes, so there is no causal genetic support. |
| mechanism | 3 | ADM is a well-characterised secreted vasodilatory peptide hormone. Its direction for ageing is unclear because the MR point estimates are non-significant and a vasodilator may be protective in the cardiovascular system. |
| tractability | 4 | A clinical-stage antibody modality is listed, and the small-molecule evidence includes ligand-bound structures. No clinical small molecule is listed. |
| safety | 3 | Open Targets lists no liabilities, but absence of data is not evidence of safety. ADM is a vasoactive hormone, so neutralising it could affect blood pressure and vascular integrity. |
| clinical precedence | 3 | One drug, the antibody enibarcimab, has reached Phase 2/3. I scored it 3 because it is not a confirmed Phase 3 or approved drug. |

**Key uncertainties:**

- Direction of effect: inhibit or activate is unresolved. Better-powered MR with more instruments, plus colocalisation, is needed.
- No colocalisation or replication of the MR instrument was returned.
- The DNAm surrogate result in schizophrenia says nothing about the causal role of the measured protein.
- Safety of long-term ADM neutralisation in healthy people is untested; no safety data were returned.

**Conflicts between sources:**

- The antibody tractability label 'Advanced Clinical' is consistent with enibarcimab at Phase 2/3. The small-molecule tractability labels (ligand-bound structures) have no matching clinical small molecule in the candidates list. I relied on the clinical candidates list for precedence.
- The disease-association scores are for cardiovascular and related disease, while the MR shows no causal effect on ageing outcomes. I treated ageing relevance as moderate and did not weight the association scores as causal.

**Claims from model knowledge, not from the evidence tools:**

- The DNAm surrogate findings describe the methylation estimate, not the measured protein.
- Circulating MR-proADM is a known prognostic biomarker of cardiovascular risk and mortality, and ADM is often considered a compensatory protective peptide.
- Adm knockout mice are embryonic lethal with cardiovascular and lymphatic defects, so full inhibition may carry risk.
- ADM has cardioprotective and vasodilatory roles.
- Enibarcimab (adrecizumab) is a non-neutralising anti-ADM antibody studied in sepsis and septic shock.

## GDF15

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

GDF15 is a secreted stress hormone that signals through GFRAL. It has a high ageing literature share, and Open Targets links it to age-related diseases at low scores. MR of the measured protein on frailty, parental longevity and GrimAge acceleration was null, so there is no genetic support for a direction. Antibody tractability is the only modality listed, no drugs are listed, and no safety liabilities are recorded, though that is absence of data. The GrimAge surrogate result does not speak to the measured protein. Recommendation: consider, as a lower-priority candidate pending better causal evidence.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | 34.7% of papers concern ageing, and it is linked to several age-related diseases, but the association scores are low. MR of the measured protein on ageing outcomes was null, which is weak evidence against a causal role. |
| mechanism | 3 | The hormone–GFRAL stress and aversion axis is well characterised. The direction for ageing is unclear: MR was null, and GDF15 may be both harmful (cachexia, nausea) and protective (tissue tolerance). |
| tractability | 3 | Only antibody tractability is listed, because the protein is secreted. There is no small-molecule evidence. PROTAC evidence is present but is of limited relevance for a secreted ligand. |
| safety | 3 | Open Targets lists no liabilities, but absence of data is not evidence of safety. The function summary points to concerns: GDF15 mediates tissue tolerance and metabolic adaptation, and inhibiting it could affect these. |
| clinical precedence | 1 | The tools list no drugs acting on GDF15. |

**Key uncertainties:**

- Direction is unclear: it is not known whether lowering or raising GDF15 slows ageing.
- MR used only 2 cis instruments with significant heterogeneity, no colocalisation and no replication.
- Whether GDF15 rises with age as a causal driver or as a compensatory stress response.
- Safety of long-term GDF15 blockade in healthy older people.

**Conflicts between sources:**

- Ageing literature share is high (0.3471), but the disease association scores are low and MR is null. I relied on MR and associations for ageing relevance.
- Tractability lists antibody evidence, but the clinical candidates list is empty. I relied on the clinical list for precedence.
- Open Targets lists no safety liabilities, while the UniProt function describes nausea/aversion and a protective role in tissue tolerance. I scored safety at 3, not 4.

**Claims from model knowledge, not from the evidence tools:**

- GDF15 is widely reported as a plasma biomarker that rises with age (not returned by the tools).
- Anti-GDF15 antibodies such as ponsegromab have been studied in cachexia. They are not listed by the tools and are not scored.

## B2M

Representative run 0 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

B2M is the MHC class I light chain and a secreted plasma protein. It is one of the GrimAge component proteins, and about 10% of its literature concerns ageing. MR could not be run because there are no cis instruments, and Open Targets lists no ageing-disease associations. Its tractability is moderate (small-molecule and antibody evidence). No drugs are listed, and no safety liabilities are listed, but its immune role warrants caution. The direction of modulation is unclear, and I recommend we consider it, with the caveat that the causal evidence is missing.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About 10% of B2M papers concern ageing, and it is a GrimAge component protein. MR was not tested and Open Targets lists no ageing-disease associations, so causal evidence is missing. |
| mechanism | 3 | B2M is well characterised as the MHC class I light chain. Its causal link to ageing and the direction of modulation are unclear because there is no MR. |
| tractability | 3 | Small-molecule evidence (structure with ligand, high-quality pocket) and antibody evidence (secreted and cell-surface localisation) exist. No approved-drug precedence is listed. |
| safety | 3 | No liabilities are listed, but absence of data is not evidence of safety. B2M is essential for MHC class I, and loss causes MHC class I deficiency, so inhibition could impair immunity. |
| clinical precedence | 1 | No drugs are listed for B2M. |

**Key uncertainties:**

- No MR of measured B2M on lifespan, frailty or GrimAge acceleration; a non-cis instrument or other causal evidence would help.
- Whether lowering circulating B2M, rather than cell-surface B2M, is safe and slows ageing.
- The Shirai finding concerns the DNAm surrogate in schizophrenia, not the measured protein.

**Conflicts between sources:**

- Literature has 3025 ageing papers (share 0.1015), yet Open Targets lists no ageing disease associations (n_ageing 0). I treated the literature as indicating interest, not causal evidence.
- Tractability lists small-molecule and antibody evidence, but the clinical candidates list is empty. I relied on the clinical list for precedence.

**Claims from model knowledge, not from the evidence tools:**

- Circulating B2M is reported to rise with age and is described in the literature as a pro-ageing factor, for example in cognition studies in mice.
- The Shirai finding concerns the DNAm surrogate, not measured protein.
- B2M forms amyloid in dialysis-related amyloidosis.
- B2M loss impairs MHC class I antigen presentation and CD8 T-cell function.

## TIMP1

Representative run 1 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

TIMP1 is a secreted MMP inhibitor with growth-factor activity. About 21% of its papers mention ageing, and it has modest associations with age-related diseases such as COPD, coronary disease and Alzheimer disease. MR could not be tested because there are no cis instruments, so causal evidence and modulation direction are missing. It has only antibody-level tractability, no clinical candidates and two generic safety liabilities. Recommendation: deprioritise.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About 21% of papers mention ageing and 12% senescence, and there are modest associations with several age-related diseases. MR could not be tested and the project context gives no result for the protein itself. |
| mechanism | 3 | The biochemistry is well characterised: TIMP1 inhibits MMPs and signals through CD63 and ITGB1. Its causal direction in ageing is unknown because MR was not tested, so the modulation direction is unclear. |
| tractability | 2 | There is no small-molecule evidence. It is a secreted protein, so an antibody is feasible in principle, and PROTAC evidence is weak. There is no approved-drug precedence. |
| safety | 2 | Open Targets lists two liabilities, both generic. TIMP1 is a broad MMP inhibitor with growth-factor activity, so systemic modulation could cause off-target effects. Without MR or other data the direction of modulation is unknown. |
| clinical precedence | 1 | No drugs are listed for TIMP1. |

**Key uncertainties:**

- Causal effect of the measured protein on ageing outcomes is unknown. Alternative instruments (trans pQTLs) or other causal evidence would resolve this.
- Whether raising or lowering TIMP1 slows ageing, given that it is both an MMP inhibitor and a signalling growth factor.
- TIMP1 is a GrimAge component but its own DNAm surrogate was not tested in schizophrenia, and the surrogate is not the measured protein.
- Safety of systemic modulation of a pleiotropic protein.

**Claims from model knowledge, not from the evidence tools:**

- TIMP1 is a component of the GrimAge plasma-protein panel (stated in project context); the surrogate result is not a result for the measured protein.
- TIMP1 is pleiotropic: it inhibits many MMPs and has growth-factor and erythropoietic activity, and it is linked to cancer biology. Broad modulation may therefore have wide effects.

## CST3

Representative run 1 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

CST3 (cystatin C) is a secreted cysteine protease inhibitor with a high ageing literature share and associations with AMD, CKD and aging. MR of the measured protein shows no Bonferroni-significant effect on parental longevity, frailty or GrimAge acceleration, and the point-estimate signs are mixed. Colocalisation and replication are not available. The project's GrimAge and schizophrenia findings concern the DNAm surrogate, not the measured protein. No drugs or safety liabilities are listed, and tractability is moderate. Recommendation: deprioritise.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 2 | Literature has a sizeable ageing share and disease associations include AMD, CKD and aging, but MR with 6 cis instruments shows no significant effect on any ageing outcome. The GrimAge and schizophrenia findings concern the methylation surrogate, not the measured protein. |
| mechanism | 2 | Function as a cysteine protease inhibitor is known, but its causal link to ageing is not shown and the direction is unclear, with MR point estimates inconsistent in sign. |
| tractability | 3 | Small-molecule evidence (structure with ligand, high-quality pocket) and antibody evidence for a secreted protein; no approved-drug precedence. |
| safety | 3 | No liabilities are listed, but absence of data is not safety. It is a protease inhibitor with amyloidosis links, and inhibiting it could be a concern. |
| clinical precedence | 1 | No drugs are listed for CST3. |

**Key uncertainties:**

- Direction of modulation is unclear; MR is null with mixed signs
- Colocalisation and replication data are missing
- Association with ageing may reflect kidney function confounding
- Safety data are absent, not evidence of safety

**Conflicts between sources:**

- Literature shows a high ageing share (0.2464) and Open Targets lists ageing-related disease associations, but MR finds no significant causal effect on ageing outcomes; I relied on MR for causal weight.
- Tractability shows small-molecule and antibody evidence, while the clinical candidates list has no drugs (max stage none); I scored precedence on the clinical list.

**Claims from model knowledge, not from the evidence tools:**

- Plasma cystatin C is widely used as a kidney function marker, which may inflate ageing literature counts via confounding.
- CST3 variants are linked to amyloid deposition (hereditary cerebral amyloid angiopathy).
- Cystatin C is an endogenous protease inhibitor; reduced function may affect protease balance and variants are linked to amyloid disease.

## LEP

Representative run 0 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

LEP (leptin) is a well-characterised secreted hormone of energy balance with a high ageing-literature share (0.23) and a T2D association (0.401). Mendelian randomisation with a single cis instrument is not significant on any outcome, and the point estimates differ in sign between outcomes. There is no colocalisation or replication. Tractability is limited to antibody-type features, there are no listed clinical drugs, and Open Targets lists weight-gain liabilities. The modulation direction is unclear. Recommendation: deprioritise.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 2 | About 23% of papers mention ageing, and there are associations with age-related disease (T2D 0.401). However, MR is null on all outcomes with inconsistent signs, and the project context shows no difference in the DNAm surrogate. The surrogate result says nothing about the measured protein. |
| mechanism | 3 | Leptin's role in energy balance, appetite and immunity is well characterised. The direction for ageing is unclear: MR point estimates conflict between lifespan/frailty (worse) and GrimAge (better), and none are significant. |
| tractability | 2 | As a secreted protein, it has only antibody-modality predicted features. There is no small molecule, PROTAC or other-modality evidence. |
| safety | 2 | Open Targets lists weight gain and extreme weight gain as liabilities. Leptin also has broad metabolic, reproductive and immune roles, so modulation would likely have wide effects. |
| clinical precedence | 1 | The tools list no drugs acting on LEP. Recombinant leptin replacement exists but is not listed, so it is not scored. |

**Key uncertainties:**

- Direction of effect: MR point estimates differ in sign across outcomes and none is significant, so it is unclear whether to inhibit or activate.
- Single cis instrument with no colocalisation, replication or sensitivity analysis.
- Whether leptin resistance rather than leptin level drives ageing-related disease; MR of LEPR or leptin signalling could help.
- The project context covers only the DNAm surrogate, and it did not differ; the measured protein was not assessed there.

**Conflicts between sources:**

- Clinical candidates list no drugs, but metreleptin (known from background, not in the tools) is approved for lipodystrophy. I relied on the tool output for scoring.
- The literature ageing share is high (0.2313), but MR is null and the ageing disease associations are modest. I weighted genetic evidence and association scores over literature volume.

**Claims from model knowledge, not from the evidence tools:**

- Large literature counts partly reflect popularity of leptin in obesity research.
- Leptin resistance in obesity (high levels with blunted signalling) complicates the direction of intervention.
- Leptin affects reproductive and immune function, so systemic modulation is likely to have wide effects.
- Metreleptin, a recombinant leptin analogue, is approved for lipodystrophy. It replaces the protein rather than modulating it, and the tools do not list it.
