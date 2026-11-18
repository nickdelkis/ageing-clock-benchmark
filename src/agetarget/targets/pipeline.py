"""Target triage, end to end: evidence, a batch of agent assessments, and the checks on a batch.

run_batch() is the only step that calls an LLM. assess() reads a saved batch and writes
to results/targets/ (or results/targets/rebuilt/<batch>/ for an earlier batch):
    baseline.csv            rule-based scores from the same evidence
    citations.csv           every cited value against the evidence the agent was shown
    run_summary.csv         per run: completed, turns, tools used, claims from model knowledge
    agreement.csv           agent vs baseline, per dimension
    ranking.csv, ranking.png
    weight_sensitivity.csv  the ranking under other weightings of the rubric
    report.md               the assessments, assembled without further LLM text
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from .. import config as cfg
from ..style import apply_style
from . import agent, causal, checks, evidence, llm, report
from .rubric import DIMENSIONS


def load_dossiers(refresh: bool = False) -> dict[str, dict]:
    """Cached evidence for every target (fetched if missing or refresh=True), with the MR results attached."""
    dossiers = {symbol: evidence.load_or_fetch(symbol, cfg.EVIDENCE_DIR, context=t["context"], aliases=t["aliases"],
                                               refresh=refresh)
                for symbol, t in cfg.TARGETS.items()}
    causal.attach(dossiers, cfg.MR_RESULTS)
    return dossiers


def batches() -> list[Path]:
    return sorted(p for p in cfg.AGENT_RUNS.iterdir() if p.is_dir()) if cfg.AGENT_RUNS.exists() else []


def run_batch(n_runs: int = cfg.N_RUNS, log: Callable[[str], None] = print) -> Path:
    """Assess every target n_runs times with the LLM configured in the environment; save the traces."""
    client = llm.from_env()
    log(f"LLM: {client.describe()}")
    dossiers = load_dossiers()
    batch = cfg.AGENT_RUNS / datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    for run in range(n_runs):
        for symbol in cfg.TARGETS:
            r = agent.assess(dossiers[symbol], client, run=run)
            results.append(r)
            status = "ok" if r.assessment else f"FAILED ({r.error})"
            log(f"run {run}  {symbol:<9} {status:<8} turns={r.n_turns}  "
                f"tools={len(set(r.tools_called))}/{len(agent.EVIDENCE_TOOLS)}")
            # A rejected request (bad key, model name or parameter) will fail for every target: stop early
            if r.error and any(f"HTTP {c}" in r.error for c in (400, 401, 403, 404)):
                agent.save_results(results, batch)
                raise SystemExit("Stopping: fix the request error above before running again.")
    agent.save_results(results, batch)
    log(f"Traces saved to {batch}")
    return batch


def mean_scores(results: list[agent.AgentResult]) -> pd.DataFrame:
    """Mean agent score per target and dimension, across runs."""
    return checks.scores_long(results).groupby(["target", "dimension"]).score.mean().unstack()[list(DIMENSIONS)]


def assess(batch: str | Path | None = None, out: Path | None = None, log: Callable[[str], None] = print) -> pd.DataFrame:
    """Check, rank and report a saved batch (default: the latest). No LLM calls."""
    apply_style()
    all_batches = batches()
    if not all_batches:
        raise SystemExit(f"No batches in {cfg.AGENT_RUNS}; run `python -m agetarget agent` first.")
    batch = Path(batch) if batch else all_batches[-1]
    if not batch.is_dir():
        batch = cfg.AGENT_RUNS / str(batch)
    latest = batch.resolve() == all_batches[-1].resolve()
    out = Path(out or (cfg.TARGET_RESULTS if latest else cfg.TARGET_RESULTS / "rebuilt" / batch.name))
    out.mkdir(parents=True, exist_ok=True)

    results = agent.load_results(batch)
    if not any(r.assessment for r in results):
        raise SystemExit(f"Batch {batch.name} has no completed assessments.")
    dossiers = load_dossiers()

    checks.baseline_table(dossiers).to_csv(out / "baseline.csv")
    citations = checks.citation_check(results, dossiers)
    citations.to_csv(out / "citations.csv", index=False)
    checks.run_summary(results).to_csv(out / "run_summary.csv", index=False)
    checks.agreement(results, dossiers).to_csv(out / "agreement.csv")
    rank = checks.ranking(results, dossiers)
    rank.to_csv(out / "ranking.csv")

    scores = mean_scores(results)
    pd.concat({label: checks.weight_sensitivity(scores, concentration=conc)
               for label, conc in [("near chosen weights", 50.0), ("any weighting", None)]},
              names=["weights", "target"]).to_csv(out / "weight_sensitivity.csv")

    model = results[0].model
    n_runs = len({r.run for r in results})
    fig = report.plot_ranking(
        rank,
        title="Agent and rule-based ranking of the GrimAge proteins as ageing targets",
        subtitle=f"{model.split(' @')[0]}, {n_runs} runs per target, batch {batch.name}. Bars show the range across runs.",
    )
    fig.savefig(out / "ranking.png")
    plt.close(fig)
    retrieved = sorted({d["retrieved"] for d in dossiers.values()})[-1]
    report.write_report(out / "report.md", rank, results, citations, model=model,
                        header=f"Candidate targets: the seven GrimAge proteins. Evidence retrieved {retrieved}.")

    counts = citations.status.value_counts().to_dict()
    log(f"Batch {batch.name}: {len(results)} results; citations {counts}; wrote {out}")
    return rank
