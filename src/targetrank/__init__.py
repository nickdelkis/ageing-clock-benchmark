"""Evidence gathering and LLM-agent assessment of candidate targets.

Two layers, kept separate on purpose:
- sources/dossier: deterministic API calls, cached to JSON (reproducible, auditable)
- agent: an LLM reads the cached evidence through tools and returns a structured,
  cited assessment; evaluate checks those citations against the evidence.
"""
