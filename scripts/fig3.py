"""Figure 3 - net figures of merit and ESM_BM across all six scenarios.

Composition panels are drawn only for mass and volume. Power is at least 100%
system in every scenario and crew time is entirely process operations, so a
composition panel for either would carry no variance.

Net values are drawn as points, not bars: on a log axis a bar's length is not
proportional to the value it encodes, so bars would misrepresent the ratios the
panel exists to show.

The net ESMBM panel that used to sit here was removed at the co-author's
request, because Figure 4b presents the same quantity. With six panels rather
than seven there is no spare cell for the key, so it runs along the bottom.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

import fombees_palette as pal
from extract_fom import CREDIT
from fig_style import (MM, ESMBM, METRIC_LABEL, SUBSCRIPT_PT, fmt,
                       panel_label, plain_log, save)
from load import totals
from read_esmbm import read as read_esm

pal.check()

tot = totals()
esm = {s: v["ESM_BM"] for s, v in read_esm().items()}
ORDER = sorted(esm, key=esm.get)                      # cheapest first, everywhere
SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}
COMPOSE = ["mass", "volume"]
STACK = ["System", "Process Operations", "Input", "Waste"]

letters = iter("abcdef")


def composition(ax, metric: str) -> None:
    ys = range(len(ORDER))
    for y, s in zip(ys, ORDER):
        gross = tot[(s, metric, "Gross")]
        if not gross:
            continue
        left = 0.0
        for flow in STACK:
            v = tot.get((s, metric, flow), 0.0)
            if not v:
                continue
            pct = 100 * v / gross
            ax.barh(y, pct, left=left, height=0.62, color=pal.FLOW[flow],
                    linewidth=0)
            # printed only where the segment can hold the digits; smaller
            # segments would overlap their neighbours
            if pct >= 9:
                ax.annotate(f"{pct:.0f}", (left + pct / 2, y), ha="center",
                            va="center", fontsize=5.0,
                            color="white" if flow == "System" else "black")
            left += pct
        credit = tot.get((s, metric, CREDIT), 0.0)
        if credit:
            cpct = 100 * credit / gross
            ax.barh(y, -cpct, height=0.62, color=pal.CREDIT, linewidth=0)
            if cpct >= 9:
                ax.annotate(f"{cpct:.0f}", (-cpct / 2, y), ha="center",
                            va="center", fontsize=5.0, color="white")
        net = 100 - 100 * credit / gross
        # marked just under the bar rather than across it: drawn over the bar
        # it landed on top of a segment's printed value
        ax.plot([net], [y + 0.46], marker="^", color=pal.NET, markersize=2.6,
                clip_on=False)
        # the net is the quantity the panel exists to show, so it is always
        # printed, clear of the bar
        ax.annotate(f"{net:.0f}", (103, y), ha="left", va="center",
                    fontsize=5.0, color=pal.NET, annotation_clip=False)
    ax.axvline(0, color="black", lw=0.5)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([SHORT.get(s, s) for s in ORDER], fontsize=5)
    ax.set_xlabel(f"% of gross {metric.replace('_', ' ')}", fontsize=6)
    ax.tick_params(axis="both", labelsize=5)
    ax.set_xlim(right=101)
    ax.invert_yaxis()


def netplot(ax, values: dict, xlabel: str, labels: bool = False) -> None:
    ys = range(len(ORDER))
    vals = [values[s] for s in ORDER]
    ax.plot(vals, list(ys), "o", color=pal.NET, markersize=2.6,
            linestyle="none")
    base = values["FLOWN"]
    if base > 0:
        ax.axvline(base, color=pal.BASELINE, lw=0.6, ls=pal.DASHED)
    pos = [v for v in vals if v > 0]
    if pos:
        ax.set_xscale("log")
        lo, hi = min(pos) / 3.2, max(pos) * 5.5
        ax.set_xlim(lo, hi)
        plain_log(ax, "x")
    for y, v in zip(ys, vals):
        if v > 0:
            ax.annotate(fmt(v), (v, y), fontsize=5.0, ha="left", va="center",
                        xytext=(3.2, 0), textcoords="offset points")
        elif pos:
            # a true zero cannot be placed on a log axis; draw it as an open
            # marker pinned to the left edge so the row is not silently blank
            ax.plot([lo], [y], marker="o", color=pal.NET, markersize=2.6,
                    markerfacecolor="white", markeredgewidth=0.6)
            ax.annotate("0", (lo, y), fontsize=5.0, ha="left", va="center",
                        xytext=(3.2, 0), textcoords="offset points")
    ax.set_yticks(list(ys))
    ax.set_yticklabels([SHORT.get(s, s) for s in ORDER] if labels
                       else [""] * len(ORDER), fontsize=5)
    ax.set_xlabel(xlabel, fontsize=6)
    ax.tick_params(axis="both", labelsize=5)
    ax.invert_yaxis()


fig = plt.figure(figsize=(183 * MM, 134 * MM))
gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.30,
                      left=0.115, right=0.985, top=0.965, bottom=0.150)


def letter(ax, dx: float) -> None:
    panel_label(fig, ax, next(letters), dx=dx, dy=0.008)


for row, metric in enumerate(COMPOSE):
    axc = fig.add_subplot(gs[row, 0])
    composition(axc, metric)
    letter(axc, 0.105)
    axn = fig.add_subplot(gs[row, 1])
    netplot(axn, {s: tot[(s, metric, "Net")] for s in ORDER},
            "Net " + METRIC_LABEL[metric])
    letter(axn, 0.028)

for col, metric in enumerate(["power", "crew_time"]):
    ax = fig.add_subplot(gs[2, col])
    netplot(ax, {s: tot[(s, metric, "Net")] for s in ORDER},
            "Net " + METRIC_LABEL[metric], labels=True)
    letter(ax, 0.105)

from matplotlib.lines import Line2D

handles = [plt.Rectangle((0, 0), 1, 1, color=pal.FLOW[f]) for f in STACK]
labels = list(STACK)
handles.append(plt.Rectangle((0, 0), 1, 1, color=pal.CREDIT))
labels.append("Useful output (credit)")
handles.append(Line2D([0], [0], marker="^", color=pal.NET, lw=0, markersize=4))
labels.append("net, printed at right")
handles.append(Line2D([0], [0], color=pal.BASELINE, lw=0.8, ls=pal.DASHED))
labels.append("FLOWN reference")
fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=5.2,
           frameon=False, bbox_to_anchor=(0.5, 0.012), handlelength=1.2,
           columnspacing=1.6, handletextpad=0.5)

save(fig, "Figure3_cross_scenario")
print("  net ESM_BM: " + "  ".join(f"{SHORT.get(s, s)[:9]} {esm[s]:,.0f}"
                                   for s in ORDER))
