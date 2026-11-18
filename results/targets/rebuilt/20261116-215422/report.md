# Target assessment report

Candidate targets: the seven GrimAge proteins. Evidence retrieved 2026-11-16.

Model: `anthropic:claude-sonnet-5-5 @ https://api.anthropic.com`. Runs per target: 3.

Citation check: 254 of 254 cited facts match the evidence exactly, 0 are close paraphrases of a text fact, 0 do not match, and 0 cite facts that do not exist (checked against the evidence the agent was shown in each run).

18 cited facts have changed in the evidence since these runs (e.g. a reworded project context).

| Rank | Target | Agent score (range) | Baseline | Recommendations across runs |
| --- | --- | --- | --- | --- |
| 1 | SERPINE1 | 3.50 (3.50-3.50) | 3.50 | prioritise 2, consider 1 |
| 2 | ADM | 3.30 (3.20-3.35) | 4.00 | consider 3 |
| 3 | GDF15 | 3.00 (3.00-3.00) | 3.45 | consider 3 |
| 4 | CST3 | 2.88 (2.80-3.00) | 3.35 | consider 2, deprioritise 1 |
| 5 | B2M | 2.50 (2.50-2.50) | 2.30 | consider 3 |
| 6 | TIMP1 | 2.33 (2.15-2.50) | 2.95 | deprioritise 3 |
| 7 | LEP | 2.30 (2.30-2.30) | 2.95 | consider 2, deprioritise 1 |

## SERPINE1

Representative run 1 (median score). **Recommendation:** prioritise. **Proposed modulation:** inhibit.

SERPINE1 (PAI-1) is a secreted serine protease inhibitor involved in senescence. About 21% of its papers mention ageing, and it is associated with cardiovascular, metabolic and neurodegenerative disease. It is also a GrimAge surrogate component. Small-molecule tractability is good, but the only clinical drug, aleplasinin, stopped at phase 1. The main concern is bleeding risk from inhibition. I would inhibit it, and I rate it worth considering to prioritise.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | High ageing/senescence literature share, UniProt role in cellular senescence, associations with several age-related diseases, and it is a GrimAge component. Disease association scores are modest, and the GrimAge link is a methylation surrogate. |
| mechanism | 4 | It is a well-characterised inhibitor of tPA/uPA and is implicated in senescence. Lowering PAI-1 activity is the likely direction, but its role in ageing is pleiotropic and partly independent of protease inhibition. |
| tractability | 4 | Small-molecule tractability is strong, with advanced clinical status, a ligand-bound structure and a high-quality pocket. Antibody tractability is also supported because the protein is secreted. No approved drug is listed. |
| safety | 3 | Open Targets lists two liabilities. The disease associations show that PAI-1 deficiency causes abnormal bleeding, so inhibition carries a bleeding risk, particularly with anticoagulants. |
| clinical precedence | 2 | The only listed drug, aleplasinin, reached phase 1. |

**Key uncertainties:**

- Whether lowering PAI-1 slows ageing in humans is unproven. The evidence is associative.
- The GrimAge link comes from DNA-methylation surrogates, not measured protein levels, and the schizophrenia difference was explained by smoking.
- The bleeding risk from inhibition and how to dose around it.
- Only phase 1 clinical experience, with no efficacy data in the tool output.

**Claims from model knowledge, not from the evidence tools:**

- The human SERPINE1 null mutation (Amish) is associated with longer lifespan and protection from diabetes (from my own knowledge, not the tools).

## ADM

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

ADM (adrenomedullin) is a secreted vasoactive peptide. It is linked to cardiovascular and renal age-related disease, and 17.7% of its papers concern ageing. It is also one of the GrimAge plasma-protein surrogates, but that link is a methylation estimate and not a measured level. It is tractable: the antibody enibarcimab has reached Phase 2/3, and small-molecule ligands exist. The direction of modulation is unclear, because ADM is cardioprotective while high plasma levels mark mortality risk. I would consider it mainly as a biomarker or a context-specific target, not as a clear ageing intervention.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | Moderate ageing share of the literature and cardiovascular and renal age-related disease associations. The project link is only a DNAm surrogate in GrimAge, which is not a measured protein level. Causality and direction are not established. |
| mechanism | 3 | The peptide hormone function is well characterised (vasodilation, MRGPRX2 ligand). Its role in ageing is unclear, and the direction is ambiguous because ADM is protective in the heart and vasculature while high circulating levels mark risk. |
| tractability | 4 | Secreted target with antibody evidence at advanced clinical stage, and small-molecule ligand structures and high-quality ligands. There is no approved drug. |
| safety | 3 | Open Targets lists no liabilities, but absence of data is not evidence of safety. ADM is a vasoactive and cardioprotective hormone, so blocking it could cause haemodynamic or cardiac effects, and chronic inhibition in healthy ageing is untested. |
| clinical precedence | 4 | One drug, the antibody enibarcimab, has reached Phase 2/3. It is not approved, and its indication is acute illness rather than ageing. |

**Claims from model knowledge, not from the evidence tools:**

- Plasma MR-proADM is a known prognostic biomarker for mortality and cardiovascular risk, and ADM is generally considered cardioprotective.
- ADM signals through CALCRL/RAMP2 and RAMP3 receptors.
- Adm knockout is embryonic lethal in mice, with hydrops fetalis and cardiovascular defects.
- Enibarcimab (adrecizumab) is a non-neutralising anti-ADM antibody studied in septic shock.

## GDF15

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

GDF15 is a secreted stress hormone acting through GFRAL. About 35% of its papers concern ageing, and it is weakly associated with several age-related diseases. It is also a GrimAge plasma-protein component. The causal role in ageing is unproven and the direction is ambiguous. Blocking it may reduce anorexia and sarcopenia, but it also has protective roles, for example in the heart and in infection tolerance. It is tractable mainly by antibody. No drugs are listed and no safety liabilities are recorded, which is a data gap rather than reassurance. I would consider it, with priority on resolving the causal direction, for example with genetics.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | A large share of GDF15 papers concern ageing, and it is linked to several age-related diseases. It is also a GrimAge plasma-protein component. However, the association scores are low, and the project's schizophrenia result was null. Whether GDF15 is causal or only a marker of ageing is unclear. |
| mechanism | 3 | The GDF15–GFRAL stress-hormone axis is well characterised, covering appetite, nausea and energy expenditure. Its role in ageing is less clear. It has context-dependent protective functions, such as tissue tolerance and cardiac protection, so the direction to modulate is uncertain. |
| tractability | 3 | There is no small-molecule evidence. The protein is secreted, so an antibody is feasible. PROTAC evidence is weak and unlikely to apply to a secreted ligand. |
| safety | 3 | Open Targets lists no safety liabilities, but absence of data is not evidence of safety. The biology suggests risks either way. Inhibition could remove tissue-protective roles, and activation causes nausea, vomiting and anorexia. |
| clinical precedence | 1 | The tools list no drugs acting on GDF15. |

**Claims from model knowledge, not from the evidence tools:**

- Circulating GDF15 rises with age and predicts mortality in human cohorts.
- Both GDF15 blockade (for example in cachexia) and GDF15 agonism (for example for obesity) are being explored.
- Neutralising antibodies to a secreted ligand are a validated modality in general.
- Chronic GDF15 elevation drives weight loss and cachexia, which is undesirable in older people.
- Anti-GDF15 or anti-GFRAL antibodies have reportedly been tested in cachexia. The tool does not list them, so they are not scored.

## CST3

Representative run 1 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

CST3 (cystatin C) is a secreted cysteine protease inhibitor. It is a strong ageing and mortality biomarker and part of the GrimAge plasma-protein set. It has good disease associations (AMD, CKD, cardiovascular disease, aging) and a 25% ageing share of its literature. Its causal role and the direction of modulation are unclear, because it could be a protective factor or only a marker confounded by kidney function and smoking. Tractability is moderate, there are no clinical drugs and no listed safety liabilities, and the amyloid-related biology calls for caution. I would deprioritise it as a direct drug target and keep it as a biomarker.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | Cystatin C is a well-known biomarker of mortality and kidney function, and it is a component of GrimAge. Open Targets links it to AMD, CKD, cardiovascular disease and aging. About 25% of its papers concern ageing. However, much of this evidence is biomarker-based rather than causal, and the GrimAge surrogate is a methylation estimate. |
| mechanism | 2 | CST3 is a secreted inhibitor of cysteine proteases, and its function is understood in general terms. Its causal role in ageing is unclear. It may be protective (anti-amyloid, anti-protease) or it may be only a marker. Variants cause amyloid disease, so the direction of modulation is unclear. |
| tractability | 3 | Small-molecule tractability evidence is present (structure with ligand, high-quality pocket). Antibody tractability is supported by secretion. There is no approved-drug precedent. The protein is a small secreted inhibitor, which makes small-molecule inhibition less natural. |
| safety | 3 | Open Targets lists no safety liabilities, but absence of data is not evidence of safety. Biology suggests caution because cystatin C is a physiological protease regulator and CST3 variants are linked to amyloid angiopathy and neurodegeneration. Inhibiting it could be harmful. |
| clinical precedence | 1 | No drugs target CST3 in the clinic. |

**Key uncertainties:**

- Is cystatin C causal in ageing, or only a biomarker confounded by kidney function, inflammation and smoking?
- Direction of modulation: raising it may be neuroprotective, while lowering it may reduce harm. This is unresolved.
- The GrimAge surrogate is a DNA-methylation estimate, not a measured protein level.
- Absence of listed safety liabilities reflects missing data, and the amyloid angiopathy variants are a concern.
- Small-molecule modulation of a small secreted inhibitor is unproven.

**Claims from model knowledge, not from the evidence tools:**

- Plasma cystatin C is an established predictor of mortality and cardiovascular risk, and it is used to estimate GFR. It is confounded by kidney function, inflammation and smoking.
- Cystatin C has been reported to be neuroprotective in Alzheimer's models and to inhibit amyloid-beta aggregation. Whether higher levels are causal for harm or are only a marker is debated.
- Loss of cystatin C function in mice and humans may increase protease activity. Cystatin C has been implicated in neuroprotection and vascular biology.

## B2M

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** inhibit.

B2M is a secreted and cell-surface MHC class I component and one of the GrimAge plasma-protein surrogates. About 10% of its literature concerns ageing, but Open Targets lists no age-related disease associations. The DNAm surrogate is not measured protein, and the schizophrenia link is largely explained by smoking. Tractability is moderate (small-molecule pocket, antibody and PROTAC features), and no drugs have reached the clinic. Safety is the main concern: B2M is essential for MHC class I, and loss of function causes immune deficiency and immunotherapy resistance. I would only pursue it as a biomarker or as selective lowering of circulating B2M, not as systemic inhibition.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | B2M is a GrimAge plasma-protein component and ~10% of its papers concern ageing, but Open Targets lists no age-related disease associations and the DNAm surrogate is not measured protein. Ageing evidence rests on literature and the clock context. |
| mechanism | 3 | B2M's role in MHC class I is well understood. Its causal role in ageing is less clear, because the protein is both a marker and a possible mediator. Lowering circulating B2M is the plausible direction, but systemic MHC-I function must be preserved. |
| tractability | 3 | Small-molecule evidence is a ligand-bound structure and a high-quality pocket. Antibody tractability is supported by the secreted and cell-surface location, and PROTAC features are present. There are no approved drugs, and the target is a small, abundant protein. |
| safety | 2 | No liabilities are listed, but absence of data is not evidence of safety. B2M is essential for MHC class I surface expression, so inhibition risks immune deficiency, as shown by the MHC class I deficiency association and the loss of antigen presentation. Loss of function in tumours also causes immunotherapy resistance. |
| clinical precedence | 1 | No drugs acting on B2M have reached the clinic according to Open Targets. |

**Key uncertainties:**

- Whether circulating B2M causes ageing phenotypes in humans or only marks them (renal function confounding).
- Whether circulating B2M can be lowered without affecting cell-surface MHC class I.
- The GrimAge DNAm surrogate is not a measured protein level.
- Evidence for harm from circulating B2M comes mainly from mouse studies.

**Claims from model knowledge, not from the evidence tools:**

- Circulating B2M rises with age and is reported in mouse studies to impair cognition and neurogenesis (Smith et al. 2015).
- B2M is a marker of renal function and mortality in older adults.
- Elevated circulating B2M is linked to dialysis-related amyloidosis and is a biomarker of ageing.
- B2M knockout mice lack CD8 T cells and have impaired immunity.
- B2M loss-of-function mutations in tumours are linked to resistance to checkpoint inhibitors.

## TIMP1

Representative run 2 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

TIMP1 is a secreted MMP inhibitor with signalling activity. It is one of the GrimAge plasma-protein surrogates and has a notable ageing literature share (about 21%). Open Targets gives modest associations with age-related diseases such as COPD, coronary artery disease and Alzheimer disease. The causal direction for ageing is unclear, because elevated TIMP1 may be a marker of remodelling or inflammation rather than a driver. No drugs and no small-molecule tractability exist, and only antibody-class tractability is listed. I recommend deprioritising it as a direct target, but it could still be useful as a biomarker.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | TIMP1 is a GrimAge plasma-protein surrogate and has a sizeable ageing literature share, with weak-to-moderate associations with several age-related diseases. The GrimAge surrogate is a methylation estimate, not a measured protein level, and it showed no significant difference in the schizophrenia meta-analysis main model. |
| mechanism | 2 | TIMP1 has a well-defined biochemistry as an MMP inhibitor and also acts as a signalling growth factor. Its causal role in ageing is unclear: it may be a marker of tissue remodelling or inflammation, or it may be protective, so the direction of modulation is not obvious. |
| tractability | 2 | Open Targets lists no small-molecule or other-modality tractability. It lists only antibody-class (secreted, extracellular) and PROTAC database-ubiquitination flags. TIMP1 is a secreted protein with a pleiotropic function, so drugging it is difficult. |
| safety | 3 | Open Targets lists two generic liabilities (gene expression and transcription factor regulation), which carry little specific information. TIMP1 broadly regulates MMP activity and extracellular matrix remodelling, so modulating it risks effects on tissue remodelling and on cancer. Data are limited, so I did not score higher. |
| clinical precedence | 1 | No drugs acting on TIMP1 are listed. |

**Key uncertainties:**

- Whether TIMP1 is causal in ageing or only a marker of inflammation and remodelling
- Direction of modulation (inhibit vs activate) is unclear
- GrimAge surrogate is a methylation estimate, not measured protein, and was not significant in the schizophrenia meta-analysis main model
- Safety profile: generic liabilities only, with likely effects on ECM remodelling and cancer biology
- No small-molecule tractability for a secreted, pleiotropic protein

**Claims from model knowledge, not from the evidence tools:**

- Circulating TIMP1 rises with age and predicts mortality and cardiovascular risk in epidemiological studies.
- Higher TIMP1 may reflect fibrosis and inflammation, but whether it drives or protects against ageing phenotypes is not settled.
- MMP inhibitors as a class caused musculoskeletal toxicity in clinical trials.
- TIMP1 is implicated in tumour biology.

## LEP

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

LEP (leptin) is a secreted hormone that controls energy balance. It is one of the plasma proteins behind the GrimAge clock, and it is linked to type 2 diabetes and cardiovascular and neurodegenerative disease. Ageing relevance is moderate and the direction of modulation is unclear, because leptin resistance and high leptin may be harmful while leptin deficiency is severe. Tractability is limited to antibody-type signals. Safety is a concern, since reducing leptin signalling risks weight gain. The tools list no clinical candidates, although metreleptin replacement is approved for lipodystrophy. I would treat LEP as a biomarker or pathway-context target rather than a direct priority.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | Leptin is a GrimAge plasma protein surrogate and is linked to several age-related diseases, with a sizeable ageing share of papers. The GrimAge component was not significantly different in the schizophrenia meta-analysis main model, and the association evidence is largely metabolic. |
| mechanism | 3 | The physiology (hypothalamic energy balance, immune and metabolic effects via LEPR) is well characterised. The direction for ageing is ambiguous: high leptin and leptin resistance are harmful, but leptin deficiency causes severe obesity. |
| tractability | 2 | Only antibody tractability signals (secreted protein localisation) are present. There is no small-molecule, PROTAC or other-modality evidence. |
| safety | 2 | Open Targets lists weight-gain liabilities, which are the obvious on-target risk of reducing leptin signalling. Leptin also has pro-inflammatory and pro-angiogenic roles, so any modulation is pleiotropic. |
| clinical precedence | 1 | The tools list no drugs acting on LEP. Metreleptin replacement exists, but it is not listed, so I did not score it. |

**Key uncertainties:**

- Direction of modulation for ageing: lowering leptin, restoring leptin sensitivity or replacing leptin
- GrimAge surrogates are methylation estimates, not measured protein levels, and the schizophrenia meta-analysis main model was not significant
- Ageing associations are mostly metabolic and may be confounded by adiposity
- No small-molecule tractability; any approach would be biologic or pathway-level

**Claims from model knowledge, not from the evidence tools:**

- Leptin resistance and hyperleptinaemia are associated with obesity and ageing; leptin signalling interacts with mTOR and inflammation.
- Hyperleptinaemia in ageing and obesity reflects leptin resistance; whether to lower leptin or restore sensitivity is unresolved.
- Leptin deficiency causes severe obesity and hyperphagia.
- Metreleptin, a recombinant leptin analogue, is approved for lipodystrophy. It is protein replacement, not an ageing therapy.
