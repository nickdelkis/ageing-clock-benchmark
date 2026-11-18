"""Command line: python -m agetarget <step>.

    clocks [COHORT ...]   clock analysis per cohort (default: all three); needs Biolearn and the data
    pool                  random-effects meta-analysis across the cohorts
    evidence [--refresh]  fetch the evidence for every target, or re-query it
    agent [--runs N]      a new batch of agent assessments (calls the LLM in .env)
    assess [--batch ID]   check, rank and report a batch (default: the latest); no LLM calls
"""

from __future__ import annotations

import argparse

from . import config as cfg


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m agetarget", description="Ageing target discovery on public data.")
    steps = parser.add_subparsers(dest="step", required=True)
    p = steps.add_parser("clocks", help="clock analysis per cohort")
    p.add_argument("cohorts", nargs="*", default=list(cfg.COHORTS), metavar="COHORT")
    steps.add_parser("pool", help="pool the cohorts")
    p = steps.add_parser("evidence", help="fetch the target evidence")
    p.add_argument("--refresh", action="store_true", help="re-query the APIs instead of using the cache")
    p = steps.add_parser("agent", help="run a batch of agent assessments (LLM)")
    p.add_argument("--runs", type=int, default=cfg.N_RUNS, help=f"runs per target (default {cfg.N_RUNS})")
    p = steps.add_parser("assess", help="check, rank and report a batch (no LLM)")
    p.add_argument("--batch", help="batch folder name in results/targets/agent_runs (default: the latest)")
    args = parser.parse_args(argv)

    if args.step == "clocks":
        from .clocks.pipeline import run_cohort
        for cohort in args.cohorts:
            run_cohort(cohort)
    elif args.step == "pool":
        from .clocks.pipeline import pool
        pool()
    elif args.step == "evidence":
        from .targets.pipeline import load_dossiers
        dossiers = load_dossiers(refresh=args.refresh)
        print("Evidence retrieved:", sorted({d["retrieved"] for d in dossiers.values()}), "->", cfg.EVIDENCE_DIR)
    elif args.step == "agent":
        from .targets.pipeline import run_batch
        run_batch(n_runs=args.runs)
    elif args.step == "assess":
        from .targets.pipeline import assess
        assess(batch=args.batch)


if __name__ == "__main__":
    main()
