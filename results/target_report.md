# Target assessment report

Rebuilt from saved batch 20261116-230637.

Model: `anthropic:claude-sonnet-5-5 @ https://api.anthropic.com`. Runs per target: 3.

Citation check: 286 of 286 cited facts match the evidence exactly, 0 are close paraphrases of a text fact, 0 do not match, and 0 cite facts that do not exist (checked against the evidence the agent was shown in each run).

| Rank | Target | Agent score (range) | Baseline | Recommendations across runs |
| --- | --- | --- | --- | --- |
| 1 | SERPINE1 | 3.37 (3.30-3.50) | 3.50 | consider 3 |
| 2 | ADM | 3.10 (3.05-3.20) | 4.00 | consider 3 |
| 3 | CST3 | 2.85 (2.55-3.00) | 3.35 | deprioritise 2, consider 1 |
| 4 | B2M | 2.70 (2.70-2.70) | 2.30 | consider 3 |
| 4 | GDF15 | 2.70 (2.70-2.70) | 3.45 | consider 3 |
| 6 | TIMP1 | 2.50 (2.50-2.50) | 2.95 | deprioritise 2, consider 1 |
| 7 | LEP | 2.30 (2.30-2.30) | 2.95 | deprioritise 3 |

## SERPINE1

Representative run 2 (median score). **Recommendation:** consider. **Proposed modulation:** inhibit.

SERPINE1 (PAI-1) is a secreted inhibitor of tPA and uPA, and it is involved in senescence. About 21% of its papers concern ageing, and it is associated with cardiovascular, metabolic and neurodegenerative diseases. Small-molecule tractability is good, and one phase 1 drug is listed, aleplasinin. The main concern is bleeding risk, since congenital deficiency causes bleeding. The GrimAge and schizophrenia findings concern the methylation surrogate and do not directly support the protein as a target. I would inhibit it, and the recommendation is to consider it.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | About 21% of papers mention ageing, and the protein is linked to senescence and to several age-related diseases. The GrimAge-surrogate finding in schizophrenia is a methylation result and does not show the protein itself drives ageing. |
| mechanism | 4 | PAI-1 is a well-characterised inhibitor of tPA and uPA that downregulates fibrinolysis, and it is implicated in cellular senescence. Lowering its activity is the likely direction, though its role in senescence is not fully resolved. |
| tractability | 4 | The small-molecule evidence is strong, including a ligand-bound structure, a high-quality pocket and an advanced-clinical label. The antibody route is plausible because the protein is secreted. A PROTAC route is less relevant for an extracellular target. |
| safety | 2 | Two liabilities are listed. Deficiency is linked to bleeding, which predicts bleeding risk with chronic inhibition, especially alongside anticoagulants. |
| clinical precedence | 2 | Only one drug is listed, and it has reached phase 1. |

**Key uncertainties:**

- Whether partial pharmacological inhibition slows ageing in humans without causing bleeding
- Causal direction of elevated PAI-1 in ageing: driver or consequence of senescence
- Whether the DNAm surrogate change tracks measured PAI-1 protein
- Why the tractability label says advanced clinical while the listed drug is only at phase 1

**Conflicts between sources:**

- Tractability lists small molecule as 'Advanced Clinical', but the clinical candidates list shows a maximum of PHASE_1 (aleplasinin). I scored clinical precedence from the candidates list.
- The literature share for ageing is about 21%, while the disease associations are modest in score (at most 0.214). The strongest associations are with coagulation, not ageing diseases.

**Claims from model knowledge, not from the evidence tools:**

- Elevated PAI-1 is associated with ageing phenotypes in humans and mice; a loss-of-function SERPINE1 variant in Amish carriers is linked to longer lifespan.
- PAI-1 is a SASP component and is induced by p53 in senescence.
- Congenital PAI-1 deficiency causes a mild-to-moderate bleeding diathesis, notably after trauma or surgery.

## ADM

Representative run 2 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

ADM (adrenomedullin) is a secreted vasodilatory peptide. It is associated with several age-related cardiovascular, renal and metabolic diseases, and about 18% of its papers concern ageing. The GrimAge evidence applies only to the DNAm surrogate, which was higher in schizophrenia in one meta-analysis. It is not evidence about measured ADM or about causal ageing effects. The target is tractable by antibody, and enibarcimab has reached phase 2/3. No safety liabilities are listed, but this is not proof of safety, and the direction of modulation is unclear. Recommendation: consider.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | Moderate ageing literature share and associations with several age-related cardiovascular, renal and metabolic diseases. The GrimAge link concerns the methylation surrogate, not measured ADM, and no direct causal ageing evidence was returned. |
| mechanism | 2 | ADM is a secreted vasodilatory peptide hormone with known physiology. Its link to ageing is correlative, and the direction to modulate is unclear because it is both protective and a disease biomarker. |
| tractability | 4 | Antibody tractability is at advanced clinical level for this secreted target. Small-molecule evidence is limited to ligand/structure data, and PROTAC evidence is weak. |
| safety | 3 | No liabilities are recorded, but absence of data is not proof of safety. ADM is a vasodilator hormone, so blocking it could affect blood pressure and vascular function. |
| clinical precedence | 3 | One antibody, enibarcimab, has reached phase 2/3. It is not approved, and the tools do not show it tested in an ageing indication. |

**Key uncertainties:**

- Whether raising or lowering ADM slows ageing; causal evidence such as Mendelian randomisation or intervention data would resolve this.
- Whether circulating ADM is a protective compensatory response or a driver of disease.
- Whether the DNAm surrogate tracks measured ADM protein levels.
- Vascular safety of chronic ADM blockade or supplementation.

**Conflicts between sources:**

- Tractability lists small-molecule ligand evidence, but the clinical candidates list contains only an antibody. I relied on the clinical list for precedence and treated small-molecule tractability as unproven.
- The safety tool lists no liabilities, but ADM's biology is vasoactive. I capped the safety score below the maximum.

**Claims from model knowledge, not from the evidence tools:**

- The GrimAge surrogate finding concerns DNA methylation estimates, not measured ADM protein, and does not show ADM drives ageing.
- Circulating ADM/MR-proADM is a known cardiovascular risk biomarker that rises in disease.
- Elevated ADM in disease is often viewed as a compensatory protective response, so inhibiting or supplementing it could each be argued.
- ADM has roles in vascular integrity, so systemic modulation could carry cardiovascular effects.
- Enibarcimab (adrecizumab) is an anti-adrenomedullin antibody studied in acute conditions such as sepsis and heart failure.

## CST3

Representative run 0 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

CST3 (cystatin C) is a secreted cysteine protease inhibitor. It has good ageing links: about 25% of its papers concern ageing, it is associated with aging, AMD and CKD, and it is a GrimAge plasma-protein component. The causal direction is unclear, because it is a biomarker of kidney function and ageing but may also be protective. Tractability is moderate, with small-molecule and antibody evidence but no clinical drugs. No safety liabilities are listed, but that is absence of data, not evidence of safety. Recommendation: consider, mainly as a biomarker or for follow-up on causal direction, not as a priority drug target.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 4 | About a quarter of CST3 papers concern ageing, and it is associated with aging, AMD, CKD and several other age-related diseases. It is also a GrimAge component. The evidence shows association, not causality. |
| mechanism | 3 | CST3 is a secreted cysteine protease inhibitor, and its amyloid-related biology is well described. Its causal role in ageing and the direction of modulation are unclear. |
| tractability | 3 | There is small-molecule evidence (structure with ligand, high-quality pocket) and antibody tractability as a secreted protein. No clinical-stage modulators exist. A small molecule or antibody would be hard to use if activation or augmentation were needed. |
| safety | 3 | Open Targets lists no liabilities, but absence of data is not evidence of safety. Inhibiting a protease inhibitor and the amyloid-forming variants suggest possible risks. |
| clinical precedence | 1 | No drugs against CST3 have reached the clinic. |

**Key uncertainties:**

- Mendelian randomisation or genetic evidence on whether higher or lower CST3 activity is causal for ageing outcomes
- Whether raised plasma CST3 is a marker of kidney function and ageing or a driver
- Whether CST3 is neuroprotective in amyloid disease, which would argue for augmentation
- Safety of modulating CST3, given the amyloidogenic variant and cathepsin regulation

**Conflicts between sources:**

- Tractability lists small-molecule evidence (Structure with Ligand, High-Quality Pocket), but the clinical candidates list has no drugs. I relied on the clinical list for precedence and treated tractability as theoretical.
- Literature shows a 24.6% ageing share, but the top disease associations are amyloidoses, not ageing diseases. The ageing literature may reflect CST3's use as a kidney-function biomarker. I weighted it as association evidence, not causal evidence.

**Claims from model knowledge, not from the evidence tools:**

- Plasma cystatin C is widely used as a biomarker of kidney function and is associated with mortality in older adults, which may inflate the ageing literature share.
- The project context concerns the DNAm surrogate, not measured CST3 protein; its surrogate was higher in schizophrenia/first-episode psychosis in Shirai et al. 2024.
- Raised plasma levels mark kidney dysfunction and ageing, but the protein may be neuroprotective (e.g. in amyloid models), so the direction is ambiguous.
- The L68Q variant causes hereditary cerebral hemorrhage with amyloidosis (Icelandic type).

## B2M

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

B2M is the secreted MHC class I light chain and one of the GrimAge plasma proteins. About 10% of its literature concerns ageing, but Open Targets lists no age-related disease associations. Its DNAm surrogate was higher in schizophrenia/FEP, which says nothing directly about the measured protein. Tractability evidence exists across several modalities, but there are no clinical candidates and the safety data are empty. The immune role of B2M is a theoretical concern. The direction of modulation is unclear, so my recommendation is consider.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About 10% of B2M papers concern ageing, and it is one of the GrimAge plasma proteins. Open Targets lists no age-related disease associations. The DNAm surrogate was higher in schizophrenia/FEP, but that is a methylation estimate, not measured protein. |
| mechanism | 3 | The core function is well understood: it is the MHC class I light chain and it is secreted. The causal link to ageing and the direction of modulation are not established. |
| tractability | 3 | Open Targets shows small-molecule evidence (structure with ligand, high-quality pocket), antibody and PROTAC evidence. None of it is clinically validated. |
| safety | 3 | No liabilities are listed, but absence of data is not evidence of safety. B2M is needed for MHC class I, and the top disease association is MHC class I deficiency, so broad inhibition could impair immunity. |
| clinical precedence | 1 | No drugs are listed for B2M. |

**Key uncertainties:**

- Whether lowering circulating B2M slows ageing in humans (causal evidence, e.g. Mendelian randomisation or interventional data)
- Whether measured B2M protein, rather than its DNAm surrogate, differs in schizophrenia
- Whether selective targeting of circulating B2M would avoid disrupting MHC class I function
- No clinical or safety data to define a therapeutic window

**Conflicts between sources:**

- Tractability lists small-molecule, antibody and PROTAC evidence, but the clinical candidates list has no drugs. I relied on the clinical list for precedence and treated tractability as unproven.
- The ageing literature share is about 10%, but Open Targets has no ageing disease associations. I treated ageing relevance as moderate.
- The safety list is empty, but the top association is MHC class I deficiency, which suggests an on-target immune liability. I scored safety as uncertain (3), not as clean.

**Claims from model knowledge, not from the evidence tools:**

- Circulating B2M rises with age and has been reported in rodent studies to impair cognition and neurogenesis (not from the tools).
- Systemic lowering of circulating B2M might be beneficial, but this is not shown in humans.
- B2M loss abolishes MHC class I surface expression, which affects antigen presentation and immune surveillance.

## GDF15

Representative run 1 (median score). **Recommendation:** consider. **Proposed modulation:** unclear.

GDF15 is a secreted stress hormone acting through GFRAL in the brainstem. A high share of its literature concerns ageing and senescence, and it has modest links to age-related diseases. Whether to inhibit or activate it to slow ageing is unclear, because it is both a stress and ageing marker and a protective tissue-tolerance factor. It is antibody-tractable, has no small-molecule evidence, no clinical candidates are listed in the tools, and no safety liabilities are recorded, though that is not proof of safety. The project context gives no support for the measured protein, since the only finding is a null result for its DNAm surrogate. Recommendation: consider.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | A large share of GDF15 papers concern ageing (35%) and senescence (20%), and it is linked to several age-related diseases, but association scores are low (about 0.1). The project's only finding is a non-significant DNAm surrogate result, which says nothing about the measured protein. |
| mechanism | 3 | The GDF15–GFRAL hormone axis in the brainstem is well characterised, covering appetite, nausea, energy expenditure and tissue tolerance. Its causal role in ageing is unclear and its effects are context-dependent (stress signal versus protective), so the direction of modulation is not clear. |
| tractability | 3 | Open Targets lists antibody tractability features for this secreted protein (and PROTAC features), but no small-molecule or other-modality evidence. Antibodies against the ligand or receptor are feasible. |
| safety | 3 | No liabilities are recorded, but absence of data is not evidence of safety. The biology suggests risks: GDF15 mediates protective tissue tolerance and metabolic adaptation, and it modulates nausea and appetite. |
| clinical precedence | 1 | The tools list no drugs acting on GDF15. Any antibody programmes known from outside the tools are not scored. |

**Key uncertainties:**

- Is GDF15 causal in ageing, or only a stress and ageing biomarker?
- Would inhibiting or activating GDF15–GFRAL signalling slow ageing? Mendelian randomisation or intervention data in older people would resolve this.
- Effects of long-term blockade on tissue tolerance, cardiac protection and infection responses.
- The DNAm surrogate result does not reflect measured plasma GDF15 levels.

**Conflicts between sources:**

- Literature gives a high ageing share (0.3471), but Open Targets ageing-disease association scores are low (about 0.1). I treated the evidence as moderate.
- Tractability lists antibody features, but the clinical candidates list is empty. I relied on the clinical candidates tool for the clinical score.
- Safety lists no liabilities, but the UniProt function describes protective roles and aversive effects. I capped safety at 3 for this reason.

**Claims from model knowledge, not from the evidence tools:**

- Circulating GDF15 is widely reported to rise with age and is a biomarker of mortality and frailty.
- Anti-GDF15 antibodies have been developed clinically (e.g. ponsegromab for cachexia); the tools do not list them, so they are not scored.

## TIMP1

Representative run 1 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

TIMP1 is a secreted MMP inhibitor and growth-factor-like protein, and one of the GrimAge plasma proteins. About 21% of its papers mention ageing, and it has modest associations with age-related diseases such as COPD, coronary disease and Alzheimer disease. Its own methylation surrogate was not significantly different in the main schizophrenia meta-analysis model, and that surrogate does not measure the protein. Tractability is limited to antibody-type features, no drugs are listed, and the direction of modulation is unclear. Safety data are generic and uninformative. I would deprioritise TIMP1 for now.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About a fifth of TIMP1 papers mention ageing, and it is linked to several age-related diseases, but association scores are low. It is a GrimAge component, but its own surrogate showed no significant difference in the main model, and that surrogate is not the measured protein. |
| mechanism | 3 | The biochemistry is well described: TIMP1 inhibits most MMPs and also acts as a growth factor through CD63 and ITGB1. Its dual roles mean it is unclear whether raising or lowering it would slow ageing. |
| tractability | 2 | There is no small-molecule or other-modality evidence. Open Targets shows only antibody-type features, based on its secreted location, and a PROTAC feature based on ubiquitination annotation. This is weak evidence for tractability. |
| safety | 3 | Open Targets lists two liabilities, both generic process terms with no specific adverse phenotype. TIMP1 is widely expressed and acts on many pathways, and absence of data is not evidence of safety. |
| clinical precedence | 1 | No drugs are listed for TIMP1 in Open Targets. |

**Key uncertainties:**

- Whether raising or lowering TIMP1 slows ageing. Mendelian randomisation or intervention data on measured plasma TIMP1 and age-related outcomes would resolve this.
- Whether circulating TIMP1 is causal or a marker of inflammation and fibrosis.
- The effect of modulating TIMP1 on MMP balance and on CD63/ITGB1 signalling in specific tissues.
- The TIMP1 surrogate's association with schizophrenia was not tested in part 1 of the project.

**Conflicts between sources:**

- Literature gives about 21% ageing share, which suggests strong ageing interest, but Open Targets age-related disease association scores are low (maximum about 0.12). I treated the evidence as moderate.
- Open Targets lists antibody and PROTAC tractability features, but the clinical candidates list has no drugs. The features are predictions and no clinical precedent exists, so I relied on the clinical list for precedence.
- The project context says the GrimAge clock as a whole is older in schizophrenia, but the TIMP1 surrogate was not tested there and was not significant in the meta-analysis. I did not apply the clock-level result to TIMP1.

**Claims from model knowledge, not from the evidence tools:**

- Plasma TIMP1 protein is reported to rise with age and is associated with fibrosis and cardiovascular risk, but I did not retrieve those studies with the tools.
- Broad MMP inhibitors have a history of musculoskeletal toxicity in trials. Recombinant protein replacement would be a different approach.
- TIMP1 is implicated in tumour biology and fibrosis, so chronic modulation in either direction could carry risk.

## LEP

Representative run 1 (median score). **Recommendation:** deprioritise. **Proposed modulation:** unclear.

LEP (leptin) is a well-characterised secreted hormone of energy balance. About 23% of its papers mention ageing, and it is associated with type 2 diabetes and other age-related diseases. The GrimAge-surrogate evidence is null: the LEP surrogate did not differ in the main model, and that says nothing about the measured protein. Tractability is limited to antibody-type evidence, with no listed drugs. Inhibition carries weight-gain liabilities, and the direction of benefit for ageing is unclear. Recommendation: deprioritise.

| Dimension | Score | Rationale |
| --- | --- | --- |
| ageing relevance | 3 | About 23% of leptin papers mention ageing, and there are associations with several age-related diseases, led by type 2 diabetes. The project context is weak: the LEP DNAm surrogate did not differ significantly in the main model, and that is a surrogate result, not a measured-protein result. The GrimAge-wide schizophrenia difference does not apply to LEP specifically. |
| mechanism | 3 | Leptin's function is well characterised: energy balance via LEPR, hypothalamic appetite control, and immune and metabolic effects. Its link to ageing is less clear, and the direction to slow ageing is ambiguous. Lowering leptin or sensitising leptin signalling are both plausible. |
| tractability | 2 | Only antibody-bucket evidence is returned, and it is based on localisation as a secreted protein. There is no small-molecule, PROTAC or other-modality evidence. |
| safety | 2 | Open Targets lists weight-gain liabilities, including extreme weight gain. Leptin is a central regulator of energy balance, so inhibition risks obesity and metabolic effects. |
| clinical precedence | 1 | The tools list no drugs acting on LEP. Scored on the tool data only. |

**Key uncertainties:**

- Whether lowering leptin or improving leptin sensitivity would slow ageing; this needs human genetic or interventional data in older adults.
- Whether circulating leptin is causal for age-related disease or a marker of adiposity.
- Whether the measured protein, not the DNAm surrogate, differs in the relevant cohorts.
- Safety of any inhibition given the weight-gain liabilities.

**Conflicts between sources:**

- Literature (23% of papers on ageing) is stronger than the disease associations and project context suggest; the surrogate was null and associations are modest, so I weighted the latter and scored ageing relevance 3.
- Tractability shows antibody-bucket features, but the clinical candidates list is empty. I relied on the tool clinical list for scoring; metreleptin is background knowledge only.

**Claims from model knowledge, not from the evidence tools:**

- Leptin resistance and altered leptin levels are reported with obesity and ageing; the search term 'leptin' may capture non-ageing contexts.
- Leptin resistance in obesity is a recognised concept, which makes the direction of modulation ambiguous.
- Metreleptin, a recombinant leptin analogue, is approved for lipodystrophy. It replaces the protein and is not listed for the target, so it was not scored.
