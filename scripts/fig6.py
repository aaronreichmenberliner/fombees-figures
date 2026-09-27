"""Figure 6 - what drives the resource cost, and how sensitive it is.

Every curve here is produced by recomputing the workbook with one input
perturbed (see sensitivity.py), not by an analytic approximation. That matters:
plant counts pass through ROUNDUP and equipment counts through CEILING, so the
real response is step-wise, and the flat segments are a genuine feature of the
model rather than an artefact.

(a) net ESMBM against the crew-time equivalency factor
(b) net ESMBM against expression level
(c) net ESMBM against the number of weekly batches flown

Panel c was previously the crew-time feasibility chart and previously lived in
Figure 7. It was moved here at the co-author's request so that Figure 6 is
entirely sensitivity analysis.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import fombees_palette as pal
from fig_style import (MM, ESMBM, KGEQ, SUBSCRIPT_PT, panel_label,
                       plain_log, save, stagger_labels)
from load import totals
from read_esmbm import read
from sensitivity import load as load_sens

pal.check()

TEQ_USED = 0.94          # Assumptions!H13
BATCHES = 86             # Assumptions!B7
SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}


tot, r, sens = totals(), read(), load_sens()
ORDER = sorted(r, key=lambda s: r[s]["ESM_BM"])


def style(s: str) -> dict:
    return {"color": pal.SCENARIO[s], "ls": pal.linestyle(s), "lw": 0.9}


fig = plt.figure(figsize=(183 * MM, 62 * MM))
gs = fig.add_gridspec(1, 3, wspace=0.60, left=0.066, right=0.925,
                      top=0.90, bottom=0.30)

# ---- (a) crew-time equivalency
ax = fig.add_subplot(gs[0, 0])
xs = sens["teq"]["values"]
for s in ORDER:
    ax.plot(xs, sens["teq"]["curves"][s], **style(s))
ax.axvline(TEQ_USED, color="black", lw=0.5, ls=pal.DOTTED)
ax.annotate(f"in use {TEQ_USED}", (TEQ_USED, 1.005), xycoords=("data", "axes fraction"),
            fontsize=5.0, ha="center", va="bottom")
ax.set_yscale("log")
plain_log(ax, "y")
ax.set_xlabel(f"crew-time equivalency factor\n({KGEQ} per CM-h)",
              fontsize=SUBSCRIPT_PT)
ax.set_ylabel(f"Net {ESMBM} ({KGEQ} per CM)", fontsize=SUBSCRIPT_PT)
ax.set_xlim(0, 4)
ax.tick_params(labelsize=5)
# labelled after the scale is set: FLOWN and VIRAL converge at the right edge
stagger_labels(ax, [(sens["teq"]["curves"][s][-1], SHORT.get(s, s),
                     pal.SCENARIO[s]) for s in ORDER], x=4.0, fontsize=5.0)
panel_label(fig, ax, "a", dx=0.062, dy=0.014)

# ---- (b) expression level
ax = fig.add_subplot(gs[0, 1])
mult = sens["expression"]["multipliers"]
flat = []
for s, curve in sens["expression"]["curves"].items():
    base_titer = sens["base_expression"][s]
    ax.plot([base_titer * m for m in mult], curve, **style(s))
    ax.plot([base_titer], [r[s]["ESM_BM"]], "o", color=pal.SCENARIO[s],
            markersize=2.4)
    if max(curve) - min(curve) < 1e-6:
        flat.append(s)
ax.axhline(r["FLOWN"]["ESM_BM"], color=pal.SCENARIO["FLOWN"], lw=0.6,
           ls=pal.DASHED)
ax.set_xscale("log")
ax.set_yscale("log")
plain_log(ax, "x")
plain_log(ax, "y")
ax.set_xlabel("PTH-Fc expression level\n(mg per kg FW)",
              fontsize=SUBSCRIPT_PT)
ax.set_ylabel(f"Net {ESMBM} ({KGEQ} per CM)", fontsize=SUBSCRIPT_PT)
ax.tick_params(labelsize=5)
for s, c in sens["expression"]["curves"].items():
    end_x = sens["base_expression"][s] * mult[-1]
    ax.annotate(SHORT.get(s, s), (end_x, c[-1]), fontsize=5.0,
                color=pal.SCENARIO[s], ha="left", va="center",
                xytext=(2.5, 0), textcoords="offset points",
                annotation_clip=False)
# B3 again: placed after the scale is set, in axes-fraction x so it cannot be
# pushed outside the view
ax.annotate("FLOWN", (0.01, r["FLOWN"]["ESM_BM"]),
            xycoords=("axes fraction", "data"), fontsize=5.0,
            color=pal.SCENARIO["FLOWN"], ha="left", va="bottom")
panel_label(fig, ax, "b", dx=0.085, dy=0.014)

# ---- (c) mission length
# System cost is paid once and process cost is paid per batch, so the ordering
# depends on how many batches are flown.
ax = fig.add_subplot(gs[0, 2])
nb = np.arange(4, 173)


def once(s):
    return r[s]["System"]


def per_batch(s):
    return (r[s]["Process Operations"] + r[s]["Process Inputs"]
            + r[s]["Waste process outputs"]
            - r[s]["Useful process outputs"]) / BATCHES


cross = []
for s in ORDER:
    ax.plot(nb, once(s) + per_batch(s) * nb, **style(s))
for s in ORDER:
    if s == "FLOWN":
        continue
    d0 = (once(s) - once("FLOWN")) + (per_batch(s) - per_batch("FLOWN")) * nb[0]
    d1 = (once(s) - once("FLOWN")) + (per_batch(s) - per_batch("FLOWN")) * nb[-1]
    if d0 * d1 < 0:
        x = nb[0] + (nb[-1] - nb[0]) * abs(d0) / (abs(d0) + abs(d1))
        cross.append((s, x))
        y = once(s) + per_batch(s) * x
        ax.plot([x], [y], "o", markerfacecolor="white",
                markeredgecolor=pal.SCENARIO[s], markeredgewidth=0.9,
                markersize=3.4)
        ax.annotate(f"{x:.0f}", (x, y), fontsize=5.0, color=pal.SCENARIO[s],
                    ha="right", va="top", xytext=(-2.5, -1.5),
                    textcoords="offset points")
ax.axvline(BATCHES, color="black", lw=0.5, ls=pal.DOTTED)
ax.set_yscale("log")
plain_log(ax, "y")
ax.annotate(f"{BATCHES} batches", (BATCHES, 1.005),
            xycoords=("data", "axes fraction"), fontsize=5.0, ha="center",
            va="bottom")
ax.set_xlabel("number of weekly batches", fontsize=SUBSCRIPT_PT)
ax.set_ylabel(f"Net {ESMBM} ({KGEQ} per CM)", fontsize=SUBSCRIPT_PT)
ax.set_xlim(4, 172)
ax.tick_params(labelsize=5)
stagger_labels(ax, [(once(s) + per_batch(s) * nb[-1], SHORT.get(s, s),
                     pal.SCENARIO[s]) for s in ORDER], x=nb[-1], fontsize=5.0)
panel_label(fig, ax, "c", dx=0.085, dy=0.014)

save(fig, "Figure6_drivers")

teq_curve = sens["teq"]["curves"]
print("  crossings of the FLOWN baseline as the crew-time factor rises:")
for s in ORDER:
    if s == "FLOWN":
        continue
    c, f = teq_curve[s], teq_curve["FLOWN"]
    for i in range(len(xs) - 1):
        if (c[i] - f[i]) * (c[i + 1] - f[i + 1]) < 0:
            x = xs[i] + (xs[i + 1] - xs[i]) * abs(c[i] - f[i]) / (
                abs(c[i] - f[i]) + abs(c[i + 1] - f[i + 1]))
            print(f"    {SHORT.get(s, s):<12} crosses at T_eq = {x:.2f}")
if flat:
    print(f"  NOTE: {', '.join(flat)} does not respond to expression level at "
          f"all - its titer is hard-coded on the sheet rather than read from "
          f"the Assumptions tab")
print(f"\n  batch-count crossings of the FLOWN reference in 4-172: "
      f"{len(cross)}")
for s, x in cross:
    print(f"    {SHORT.get(s, s):<12} crosses at {x:.1f} batches")
