"""Target triage: evidence in code, judgement by an LLM agent, checks in code.

sources, http  API calls to Open Targets, UniProt, Europe PMC and Ensembl
evidence       per-target evidence, cached as JSON and flattened into citable facts
causal         Mendelian randomisation results (from mr/) as facts
llm, agent     the provider-agnostic client and the tool-using assessment agent
rubric         the five scored dimensions, their weights and the rule-based baseline
checks         citation check, agreement with the baseline, stability, weight sensitivity
report         ranking figure and markdown report
pipeline       load_dossiers(), run_batch() and assess(): everything above, end to end
"""
