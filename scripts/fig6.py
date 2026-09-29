"""Figure 6 - what drives the resource cost, and how sensitive it is.

(a) net ESMBM against the crew-time equivalency factor
(b) net ESMBM against PTH-Fc expression level
(c) net ESMBM against the weekly dose
(d) net ESMBM against the number of weekly batches flown

Every curve is produced by recomputing the workbook with one input perturbed
(see sensitivity.py), not by an analytic approximation. That matters more than
it sounds. An earlier version of the batch panel modelled each scenario as
system cost paid once plus process cost paid per batch. For four scenarios that
is exactly right; for GENE GUN it is badly wrong, because its equipment counts
step with batch number, and it overstated GENE GUN by 95% at 20 batches. The
visible steps in these curves are real, and no smooth formula reproduces them.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import fombees_palette as pal
from fig_style import (MM, ESMBM, KGEQ, SUBSCRIPT_PT, panel_label, plain_log,
                       save, stagger_labels)
from read_esmbm import read
from sensitivity import load as load_sens

pal.check()

TEQ_USED = 0.94          # Assumptions!H13
DOSE_USED = 5.0          # Assumptions!B8
BATCHES_USED = 86        # Assumptions!B7
SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}

r, sens = read(), load_sens()
ORDER = sorted(r, key=lambda s: r[s]["ESM_BM"])
YLAB = f"Net {ESMBM} ({KGEQ} per CM)"


def style(s: str) -> dict:
    return {"color": pal.SCENARIO[s], "ls": pal.linestyle(s), "lw": 0.9}


def crossings(xs, curves, ref="FLOWN"):
    """Where each scenario crosses the reference, by linear interpolation."""
    out = []
    for s, c in curves.items():
        if s == ref:
            continue
        f = curves[ref]
        for i in range(len(xs) - 1):
            a, b = c[i] - f[i], c[i + 1] - f[i + 1]
            if a * b < 0:
                out.append((s, xs[i] + (xs[i + 1] - xs[i])
                            * abs(a) / (abs(a) + abs(b))))
    return out


fig = plt.figure(figsize=(183 * MM, 126 * MM))
gs = fig.add_gridspec(2, 2, hspace=0.58, wspace=0.34,
                      left=0.085, right=0.885, top=0.970, bottom=0.145)

PANELS = [
    ("a", "teq", f"crew-time equivalency factor\n({KGEQ} per CM-h)",
     False, TEQ_USED),
    ("b", "expression", "PTH-Fc expression level\n(mg per kg FW)",
     True, None),
    ("c", "dose", "weekly dose (mg PTH-Fc per CM)", True, DOSE_USED),
    ("d", "batches", "number of weekly batches", False, BATCHES_USED),
]

found = {}
for i, (letter, key, xlabel, logx, marker) in enumerate(PANELS):
    ax = fig.add_subplot(gs[i // 2, i % 2])

    if key == "expression":
        # each scenario is swept over its own titer range, so the curves span
        # different x-domains and each label belongs at its own curve's end
        for s, c in sens["expression"]["curves"].items():
            xs = [sens["base_expression"][s] * m
                  for m in sens["expression"]["multipliers"]]
            ax.plot(xs, c, **style(s))
            ax.plot([sens["base_expression"][s]], [r[s]["ESM_BM"]], "o",
                    color=pal.SCENARIO[s], markersize=2.4)
            ax.annotate(SHORT.get(s, s), (xs[-1], c[-1]), fontsize=5.0,
                        color=pal.SCENARIO[s], ha="left", va="center",
                        xytext=(2.5, 0), textcoords="offset points",
                        annotation_clip=False)
        ax.axhline(r["FLOWN"]["ESM_BM"], color=pal.SCENARIO["FLOWN"], lw=0.6,
                   ls=pal.DASHED)
        ax.set_xscale("log")
    else:
        xs = sens[key]["values"]
        curves = sens[key]["curves"]
        for s in ORDER:
            ax.plot(xs, curves[s], **style(s))
        if marker is not None:
            ax.axvline(marker, color="black", lw=0.5, ls=pal.DOTTED)
        if logx:
            ax.set_xscale("log")
        found[key] = crossings(xs, curves)
        for s, x in found[key]:
            y = curves[s][0]
            for j in range(len(xs) - 1):
                if xs[j] <= x <= xs[j + 1]:
                    t = (x - xs[j]) / (xs[j + 1] - xs[j])
                    y = curves[s][j] + t * (curves[s][j + 1] - curves[s][j])
            ax.plot([x], [y], "o", markerfacecolor="white",
                    markeredgecolor=pal.SCENARIO[s], markeredgewidth=0.9,
                    markersize=3.4)

    ax.set_yscale("log")
    plain_log(ax, "y")
    if logx:
        plain_log(ax, "x")
    ax.set_xlabel(xlabel, fontsize=SUBSCRIPT_PT)
    ax.set_ylabel(YLAB, fontsize=SUBSCRIPT_PT)
    ax.tick_params(labelsize=5)

    if key != "expression":
        xs = sens[key]["values"]
        stagger_labels(ax, [(sens[key]["curves"][s][-1], SHORT.get(s, s),
                             pal.SCENARIO[s]) for s in ORDER],
                       x=xs[-1], fontsize=5.0)
    if marker is not None and key != "expression":
        lab = {"teq": f"in use {TEQ_USED}", "dose": f"{DOSE_USED:g} mg",
               "batches": f"{BATCHES_USED} batches"}[key]
        ax.annotate(lab, (marker, 1.005), xycoords=("data", "axes fraction"),
                    fontsize=5.0, ha="center", va="bottom")
    panel_label(fig, ax, letter, dx=0.070, dy=0.014)

# A key, because the figure carries four distinct marks and nothing named any
# of them. Note the base case appears two ways and has to: in a, c and d every
# scenario shares one value so it is a rule, whereas in b each scenario has its
# own titer so it has to be a point per curve.
key = [
    (Line2D([0], [0], color=pal.SCENARIO["FLOWN"], lw=0.9, ls=pal.DASHED),
     "FLOWN, the reference"),
    (Line2D([0], [0], color="black", lw=0.5, ls=pal.DOTTED),
     "value used in this study (a, c, d)"),
    (Line2D([0], [0], color=pal.SCENARIO["VIRAL"], lw=0, marker="o",
            markersize=3.4), "base case for that scenario (b)"),
    (Line2D([0], [0], color=pal.SCENARIO["VIRAL"], lw=0, marker="o",
            markersize=3.4, markerfacecolor="white", markeredgewidth=0.9),
     "crosses the FLOWN reference"),
]
fig.legend([h for h, _ in key], [l for _, l in key], loc="lower center",
           ncol=4, fontsize=5.4, frameon=False, bbox_to_anchor=(0.5, 0.030),
           handlelength=1.8, columnspacing=1.8, handletextpad=0.6)
fig.text(0.5, 0.008,
         "Curve colour identifies the scenario and is the same in every panel; "
         "each curve is labelled directly at its right-hand end.",
         ha="center", fontsize=5.2)

save(fig, "Figure6_drivers")
for key, label in (("teq", "crew-time equivalency factor"),
                   ("dose", "weekly dose (mg)"),
                   ("batches", "weekly batches")):
    if found.get(key):
        print(f"  crossings of the FLOWN reference against {label}:")
        for s, x in found[key]:
            print(f"    {SHORT.get(s, s):<12} at {x:,.1f}")
    else:
        print(f"  no crossing of the FLOWN reference against {label}")
