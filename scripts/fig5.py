"""Figure 5 - what the single-resource view gets wrong.

(a) the fraction of each scenario's gross cost returned as useful output, per
    figure of merit and for ESM_BM
(b) each scenario's rank under each single-resource constraint and under ESM_BM

The ESM_BM decomposition that used to sit here as a third panel was the same
chart as Figure 4a, minus the credit, and has been dropped rather than shown
twice. What remains is the argument this figure exists to make: the in-situ
recovery benefit is confined to mass and volume, and no single resource
reproduces the ESM_BM ordering.

Set at full 183 mm width, matching every other figure in the set. The earlier
1.5-column version left this one figure narrower than its siblings, so the
journal scaling it to full width would have made its type visibly larger than
the identical labels in Figures 2-4.

Row and column labels are one size throughout. They sit at SUBSCRIPT_PT
because one column is ESM_BM: a mathtext subscript renders at exactly 0.700 of
the base, so a 5 pt label would put the "BM" at 3.5 pt. Sizing that one label
alone made it tower over its neighbours, so the whole set moves together.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import fombees_palette as pal
from extract_fom import CREDIT
from fig_style import MM, ESMBM, SUBSCRIPT_PT, panel_label, save
from load import METRICS, totals
from read_esmbm import read

pal.check()

SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}
NICE = {"mass": "Mass", "volume": "Volume", "power": "Power",
        "crew_time": "Crew time"}

tot, r = totals(), read()
ORDER = sorted(r, key=lambda s: r[s]["ESM_BM"])
COLS = METRICS + ["esm"]

fig = plt.figure(figsize=(183 * MM, 66 * MM))
gs = fig.add_gridspec(1, 2, wspace=0.42, left=0.105, right=0.99,
                      top=0.86, bottom=0.26)


def matrix(ax, data, text, cmap, vmin, vmax, title, white_above):
    ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.annotate(text(i, j), (j, i), ha="center", va="center",
                        fontsize=6.0,
                        color="white" if white_above(data[i, j]) else "black")
    ax.set_xticks(range(len(COLS)))
    ax.set_xticklabels([NICE.get(c, ESMBM) for c in COLS],
                       fontsize=SUBSCRIPT_PT, rotation=35, ha="right")
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([SHORT.get(s, s) for s in ORDER],
                       fontsize=SUBSCRIPT_PT)
    ax.set_title(title, fontsize=SUBSCRIPT_PT, pad=5)
    ax.tick_params(length=0)


# ---- (a) useful-output recovery
recovery = np.zeros((len(ORDER), len(COLS)))
for i, s in enumerate(ORDER):
    for j, m in enumerate(METRICS):
        g = tot[(s, m, "Gross")]
        recovery[i, j] = 100 * tot.get((s, m, CREDIT), 0.0) / g if g else 0.0
    recovery[i, -1] = 100 * r[s]["Useful process outputs"] / r[s]["GROSS"]

ax = fig.add_subplot(gs[0, 0])
matrix(ax, recovery, lambda i, j: f"{recovery[i, j]:.0f}", "Greens", 0, 100,
       "% of gross returned as useful output", lambda v: v > 55)
panel_label(fig, ax, "a", dx=0.090, dy=0.016)

# ---- (b) rank under each constraint
ranks = np.zeros((len(ORDER), len(COLS)), dtype=int)
for j, m in enumerate(METRICS):
    order = sorted(ORDER, key=lambda s: tot[(s, m, "Net")])
    for i, s in enumerate(ORDER):
        ranks[i, j] = order.index(s) + 1
for i, s in enumerate(ORDER):
    ranks[i, -1] = ORDER.index(s) + 1

ax = fig.add_subplot(gs[0, 1])
matrix(ax, ranks, lambda i, j: str(ranks[i, j]), "cividis_r", 1, len(ORDER),
       "rank, 1 = lowest cost", lambda v: v > 3)
panel_label(fig, ax, "b", dx=0.090, dy=0.016)

save(fig, "Figure5_ESM_BM_vs_FOM")
print("  recovery, % of gross returned as useful output:")
for i, s in enumerate(ORDER):
    print(f"   {SHORT.get(s, s):<12}" + "  ".join(
        f"{NICE.get(c, 'ESMBM')[:9]:>9} {recovery[i, j]:>5.1f}"
        for j, c in enumerate(COLS)))
