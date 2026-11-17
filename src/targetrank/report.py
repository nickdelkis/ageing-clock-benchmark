"""Ranking figure and a markdown report assembled from the agent's structured output.

The report is built deterministically from the assessments and the citation check,
so nothing in it is free text generated after the evidence review.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from clockbench.plots import GRID, INK, INK_2, SERIES, SURFACE

import re

from .agent import AgentResult
from .rubric import DIMENSIONS


_STOP = set("""a an the and or of in on at to for from by with as is are was were be been it its this that these
those not no so than then into via can could may might also which who whose has have had do does did their there
e g eg ie i we our them they it its neither nor""".split())


def _content_words(text: str) -> set[str]:
    t = text.lower().replace("haem", "hem").replace("ageing", "aging")
    words = re.findall(r"[a-z0-9-]+", t)
    def stem(w: str) -> str:
        if len(w) > 4 and w.endswith("ies"):
            return w[:-3] + "y"
        return w.rstrip("s") if len(w) > 3 else w
    return {stem(w) for w in words if w not in _STOP}


def dedupe(items: list[str], overlap: float = 0.6) -> list[str]:
    """Drop statements that repeat an earlier one, keeping the first.

    Two statements count as repeats when most content words of the shorter one also appear in the
    longer one (e.g. the same drug, mechanism or variant described twice in different words).
    """
    kept, words_kept = [], []
    for item in items:
        w = _content_words(item)
        if any(w and k and len(w & k) / min(len(w), len(k)) >= overlap for k in words_kept):
            continue
        kept.append(item)
        words_kept.append(w)
    return kept


def plot_ranking(rank: pd.DataFrame, title: str, subtitle: str):
    """Agent overall score per target (mean, with min-max across runs) next to the rule-based baseline."""
    r = rank.sort_values("agent_overall")
    y = np.arange(len(r))
    fig, ax = plt.subplots(figsize=(7.4, 0.5 * len(r) + 1.9))
    ax.hlines(y, r["agent_min"], r["agent_max"], color=SERIES[0], lw=2, zorder=2)
    ax.scatter(r["agent_overall"], y, s=40, color=SERIES[0], edgecolor=SURFACE, linewidth=1, zorder=3,
               label="Agent (mean, range across runs)")
    # hollow and larger, drawn on top: when both scores are equal the dot shows inside the diamond
    ax.scatter(r["baseline_overall"], y, s=110, facecolor="none", edgecolor=SERIES[1], linewidth=1.8, zorder=4,
               marker="D", label="Rule-based baseline")
    for i in range(1, len(r)):
        ax.axhline(i - 0.5, color=GRID, lw=0.8, zorder=0)
    ax.set_yticks(y, r.index)
    ax.set_ylim(-0.6, len(r) - 0.4)
    ax.set_xlim(1, 5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Overall priority score (weighted, 1-5)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, handletextpad=0.3, columnspacing=1.4)
    t = fig.suptitle(title, x=0.02, ha="left", fontsize=12, fontweight="bold", color=INK)
    ax.set_title(subtitle, loc="left", fontsize=8.5, fontweight="normal", color=INK_2, pad=10)
    fig.tight_layout()
    t.set_x(ax.get_position().x0)
    return fig


def representative(results: list[AgentResult], target: str) -> AgentResult | None:
    """The completed run whose overall score is the median for this target."""
    from .rubric import overall
    done = [r for r in results if r.target == target and r.assessment]
    if not done:
        return None
    done.sort(key=lambda r: overall({d: r.assessment["scores"][d]["score"] for d in DIMENSIONS}))
    return done[len(done) // 2]


def write_report(path: Path, rank: pd.DataFrame, results: list[AgentResult], citations: pd.DataFrame,
                 model: str, header: str = "") -> Path:
    lines = ["# Target assessment report", "", header, "",
             f"Model: `{model}`. Runs per target: {max((r.run for r in results), default=0) + 1}.", ""]
    if not citations.empty:
        c = citations.status.value_counts()
        lines += [f"Citation check: {c.get('match', 0)} of {len(citations)} cited facts match the evidence exactly, "
                  f"{c.get('approximate', 0)} are close paraphrases of a text fact, {c.get('mismatch', 0)} do not match, "
                  f"and {c.get('unknown fact', 0)} cite facts that do not exist.", ""]
    lines += ["| Rank | Target | Agent score (range) | Baseline | Recommendations across runs |", "| --- | --- | --- | --- | --- |"]
    for t, row in rank.iterrows():
        recs = row.get("recommendation_counts", row.recommendation)
        lines.append(f"| {row.agent_rank} | {t} | {row.agent_overall:.2f} ({row.agent_min:.2f}-{row.agent_max:.2f}) "
                     f"| {row.baseline_overall:.2f} | {recs} |")
    for t in rank.index:
        rep = representative(results, t)
        if rep is None:
            continue
        a = rep.assessment
        lines += ["", f"## {t}", "", f"Representative run {rep.run} (median score). "
                  f"**Recommendation:** {a['recommendation']}. "
                  f"**Proposed modulation:** {a['proposed_modulation']}.", "", a["summary"], "",
                  "| Dimension | Score | Rationale |", "| --- | --- | --- |"]
        for d in DIMENSIONS:
            s = a["scores"][d]
            lines.append(f"| {d.replace('_', ' ')} | {s['score']} | {s['rationale']} |")
        if a.get("key_uncertainties"):
            lines += ["", "**Key uncertainties:**", ""] + [f"- {u}" for u in a["key_uncertainties"]]
        if a.get("source_conflicts"):
            lines += ["", "**Conflicts between sources:**", ""] + [f"- {c}" for c in a["source_conflicts"]]
        bg = dedupe([b for s in a["scores"].values() for b in s.get("background_knowledge") or []])
        if bg:
            lines += ["", "**Claims from model knowledge, not from the evidence tools:**", ""] + [f"- {b}" for b in bg]
        bad = citations[(citations.target == t) & (citations.run == rep.run) & (~citations.status.isin(["match", "approximate"]))]
        if not bad.empty:
            lines += ["", "**Citation problems in this run:**", ""] + [
                f"- `{r.fact_id}`: cited {r.cited!r}, evidence says {r.actual!r} ({r.status})" for r in bad.itertuples()]
    path = Path(path)
    path.write_text("\n".join(lines) + "\n")
    return path
