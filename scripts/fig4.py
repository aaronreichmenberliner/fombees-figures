"""Figure 4 - batch-manufacturing equivalent system mass, ESM_BM.

(a) decomposes each scenario's gross cost into the five terms of Eq. 1, with the
useful-output credit drawn left of zero and a tick marking the net.
(b) is the net on a log axis against the FLOWN baseline.

Percentages are of GROSS, not net: for two scenarios the system term alone
exceeds the net, so "% of net" would exceed 100 and stop meaning anything.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import fombees_palette as pal
from fig_style import (MM, ESMBM, KGEQ, SUBSCRIPT_PT, fmt, panel_label,
                       plain_log, save)
from read_esmbm import read

pal.check()

TERMS = ["System", "Process Operations", "Process Inputs",
         "Waste process outputs"]
CREDIT_TERM = "Useful process outputs"
SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}

r = read()
ORDER = sorted(r, key=lambda s: r[s]["ESM_BM"])

fig = plt.figure(figsize=(183 * MM, 68 * MM))
gs = fig.add_gridspec(1, 2, wspace=0.22, left=0.105, right=0.985,
                      top=0.88, bottom=0.30)

# ---- (a) composition
ax = fig.add_subplot(gs[0, 0])
for y, s in enumerate(ORDER):
    gross = r[s]["GROSS"]
    left = 0.0
    for term in TERMS:
        v = r[s][term]
        if not v:
            continue
        pct = 100 * v / gross
        ax.barh(y, pct, left=left, height=0.62, color=pal.FLOW[term],
                linewidth=0)
        if pct >= 9:
            ax.annotate(f"{pct:.0f}", (left + pct / 2, y), ha="center",
                        va="center", fontsize=5.0,
                        color="white" if term == "System" else "black")
        left += pct
    credit = r[s][CREDIT_TERM]
    if credit:
        cpct = 100 * credit / gross
        ax.barh(y, -cpct, height=0.62, color=pal.CREDIT, linewidth=0)
        if cpct >= 9:
            ax.annotate(f"{cpct:.0f}", (-cpct / 2, y), ha="center",
                        va="center", fontsize=5.0, color="white")
    net_pct = 100 * r[s]["ESM_BM"] / gross
    # marked just under the bar rather than across it: drawn over the bar it
    # landed on top of a segment's printed value
    ax.plot([net_pct], [y + 0.46], marker="^", color=pal.NET, markersize=2.8,
            clip_on=False)
    ax.annotate(f"{net_pct:.0f}", (103, y), ha="left", va="center",
                fontsize=5.0, color=pal.NET, annotation_clip=False)
ax.axvline(0, color="black", lw=0.5)
ax.set_yticks(range(len(ORDER)))
ax.set_yticklabels([SHORT.get(s, s) for s in ORDER], fontsize=5.4)
ax.set_xlabel(f"% of gross {ESMBM}", fontsize=SUBSCRIPT_PT)
ax.tick_params(labelsize=5)
ax.set_xlim(right=101)
ax.invert_yaxis()
panel_label(fig, ax, "a", dx=0.098, dy=0.012)

handles = [plt.Rectangle((0, 0), 1, 1, color=pal.FLOW[t]) for t in TERMS]
handles.append(plt.Rectangle((0, 0), 1, 1, color=pal.CREDIT))
handles.append(Line2D([0], [0], marker="^", color=pal.NET, lw=0,
                      markersize=4))
fig.legend(handles,
           TERMS + ["Useful output (credit)", "net, printed at right"],
           loc="lower center",
           ncol=5, fontsize=5.2, frameon=False, bbox_to_anchor=(0.5, 0.015),
           handlelength=1.1, columnspacing=1.3, handletextpad=0.5)

# ---- (b) net
ax = fig.add_subplot(gs[0, 1])
vals = [r[s]["ESM_BM"] for s in ORDER]
ax.plot(vals, range(len(ORDER)), "o", color=pal.NET, markersize=2.8,
        linestyle="none")
ax.axvline(r["FLOWN"]["ESM_BM"], color=pal.BASELINE, lw=0.6, ls=pal.DASHED)
for y, v in enumerate(vals):
    ax.annotate(fmt(v), (v, y), fontsize=5.0, ha="left", va="center",
                xytext=(3.4, 0), textcoords="offset points")
ax.set_xscale("log")
ax.set_xlim(min(vals) / 3.0, max(vals) * 6.0)
plain_log(ax, "x")
ax.set_yticks(range(len(ORDER)))
ax.set_yticklabels([""] * len(ORDER))
ax.set_xlabel(f"Net {ESMBM} ({KGEQ} per CM)", fontsize=SUBSCRIPT_PT)
ax.tick_params(labelsize=5)
ax.invert_yaxis()
panel_label(fig, ax, "b", dx=0.026, dy=0.012)

save(fig, "Figure4_ESM_BM")
for s in ORDER:
    g = r[s]["GROSS"]
    print(f"  {s:<20}{r[s]['ESM_BM']:>10,.0f}   proc ops {100*r[s]['Process Operations']/g:>5.1f}%"
          f"   system {100*r[s]['System']/g:>5.1f}%")
