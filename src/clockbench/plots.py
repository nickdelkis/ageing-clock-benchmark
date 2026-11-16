"""The three figures of the benchmark, in one consistent style.

Colours: a validated categorical palette (blue, orange for two groups), a
blue-grey-red diverging map for correlations, ink colours for text.
"""

from __future__ import annotations

import math
from typing import Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from .analysis import AGE, PACE

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
NEUTRAL = "#f0efec"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # first three slots: safe for scatter
POINT = "#2a78d6"

DIVERGING = LinearSegmentedColormap.from_list(
    "blue_grey_red", ["#184f95", "#6da7ec", NEUTRAL, "#ee8b8a", "#b82c2c"]
)


def apply_style() -> None:
    """Quiet axes, recessive grid, readable type."""
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "font.size": 9,
            "figure.dpi": 110,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        }
    )


def plot_predicted_vs_age(
    predictions: pd.DataFrame,
    age: pd.Series,
    kinds: Mapping[str, str],
    metrics: pd.DataFrame | None = None,
    groups: pd.Series | None = None,
    group_order: list[str] | None = None,
):
    """Small multiples: each clock against chronological age.

    Age clocks get the identity line (perfect agreement). Pace clocks get a
    line at 1.0 (one biological year per calendar year).
    """
    clocks = list(predictions.columns)
    ncol = min(3, len(clocks))
    nrow = math.ceil(len(clocks) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.3 * ncol, 3.1 * nrow), squeeze=False)
    df_age = age.astype(float)

    for ax, clock in zip(axes.flat, clocks):
        df = pd.concat({"pred": predictions[clock], "age": df_age}, axis=1, join="inner").dropna()
        kind = kinds.get(clock, AGE)
        if groups is not None and group_order:
            g = groups.reindex(df.index).astype("string")
            for i, level in enumerate(group_order):
                sel = g == level
                ax.scatter(df.loc[sel, "age"], df.loc[sel, "pred"], s=22, color=SERIES[i],
                           edgecolor=SURFACE, linewidth=0.6, label=str(level), zorder=3)
        else:
            ax.scatter(df["age"], df["pred"], s=22, color=POINT, edgecolor=SURFACE, linewidth=0.6, zorder=3)

        lo, hi = df["age"].min(), df["age"].max()
        if kind == AGE:
            span = [min(lo, df["pred"].min()), max(hi, df["pred"].max())]
            ax.plot(span, span, ls="--", lw=1, color=INK_2, zorder=2)
            ax.set_ylabel("Predicted age (years)")
        else:
            ax.axhline(1.0, ls="--", lw=1, color=INK_2, zorder=2)
            ax.set_ylabel("Pace of ageing (years per year)")
        ax.set_xlabel("Chronological age (years)")
        ax.set_title(clock, loc="left")

        if metrics is not None and clock in metrics.index:
            m = metrics.loc[clock]
            text = f"r = {m['pearson_r']:.2f}"
            if kind == AGE and not np.isnan(m["mae_years"]):
                text += f"\nMAE = {m['mae_years']:.1f} y"
            ax.text(0.03, 0.97, text, transform=ax.transAxes, va="top", ha="left", color=INK_2, fontsize=8)

    for ax in list(axes.flat)[len(clocks):]:
        ax.set_visible(False)
    if groups is not None and group_order:
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper right", ncol=len(labels), bbox_to_anchor=(1.0, 1.02))
    fig.suptitle("Each clock against chronological age", x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout()
    return fig


def plot_deviation_heatmap(corr: pd.DataFrame, method: str = "Spearman"):
    """Correlation of age deviations between clocks: do they agree on who ages fast?"""
    n = len(corr)
    fig, ax = plt.subplots(figsize=(1.0 * n + 2.2, 0.9 * n + 1.4))
    im = ax.imshow(corr.to_numpy(), cmap=DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(n), corr.columns, rotation=40, ha="right")
    ax.set_yticks(range(n), corr.index)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # white gaps between cells
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for i in range(n):
        for j in range(n):
            v = corr.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(v) > 0.6 else INK)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(labelsize=8, colors=INK_2)
    cbar.set_label(f"{method} correlation of age deviation", color=INK_2, fontsize=8)
    ax.set_title("Do the clocks agree on who is ageing fast?", loc="left")
    fig.tight_layout()
    return fig


def plot_group_forest(results: pd.DataFrame, case: str, control: str):
    """Effect size of the condition on each clock's age deviation, with 95% CI."""
    res = results.dropna(subset=["cohens_d"]).sort_values("cohens_d")
    n = len(res)
    fig, ax = plt.subplots(figsize=(6.4, 0.45 * n + 1.5))
    y = np.arange(n)
    ax.axvline(0, color=INK_2, lw=1, zorder=1)
    ax.hlines(y, res["d_ci_low"], res["d_ci_high"], color=INK, lw=2, zorder=2)
    ax.scatter(res["cohens_d"], y, s=48, color=POINT, edgecolor=SURFACE, linewidth=1.2, zorder=3)
    ax.set_yticks(y, res.index)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Cohen's d of age deviation ({case} minus {control}), 95% CI")
    q_col = "q_welch" if "q_welch" in res else None
    if q_col:
        x_text = ax.get_xlim()[1]
        for yi, q in zip(y, res[q_col]):
            ax.text(x_text, yi, f"  q = {q:.2g}", va="center", ha="left", color=INK_2, fontsize=8)
    ax.set_title(f"Is the clock older in {case} than in {control}?", loc="left")
    fig.tight_layout()
    return fig
