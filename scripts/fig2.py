"""Figure 2 - figures of merit resolved by resource group, one column per scenario.

Rows are the four FOMs; columns the six scenarios. Each bar is split by resource
group. The useful output is a credit and is drawn downward from the zero rule,
because it is subtracted in the net; drawing it upward alongside the costs would
imply it adds to them.

Panel y-axes are independent: the scenarios span more than three orders of
magnitude, so a shared scale would flatten five of the six columns into nothing.
The scale is therefore printed on every panel.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

import fombees_palette as pal
from extract_fom import CREDIT, SCEN
from fig_style import MM, fmt, panel_label, save
from load import METRICS, by_group

pal.check()

FLOW_ABBR = [("System", "S"), ("Input", "I"), ("Process Operations", "P"),
             ("Waste", "W"), (CREDIT, "O")]
ROW_LABEL = {"mass": "mass\n(kg per CM)", "volume": "volume\n(m³ per CM)",
             "power": "power\n(kW per CM)", "crew_time": "crew time\n(CM-h per CM)"}
SHORT = {"TRANSGENIC-LETTUCE": "T-LETTUCE", "TRANSGENIC-TOBACCO": "T-TOBACCO"}

g = by_group()
GROUPS = list(pal.RESOURCE)

fig = plt.figure(figsize=(183 * MM, 150 * MM))
gs = fig.add_gridspec(4, 6, hspace=0.55, wspace=0.42,
                      left=0.075, right=0.995, top=0.955, bottom=0.10)

LETTERS = "abcdefghijklmnopqrstuvwxyz"

for col, scen in enumerate(SCEN):
    for row, metric in enumerate(METRICS):
        ax = fig.add_subplot(gs[row, col])

        # which flows carry anything at all for this scenario/metric
        present = [(f, ab) for f, ab in FLOW_ABBR
                   if any(g.get((scen, metric, f, gr), 0.0) for gr in GROUPS)]
        if not present:
            # a structural zero still needs the right flow letter: crew time is
            # a process-operations term, everything else is a system term
            present = [("Process Operations", "P")] if metric == "crew_time" \
                else [("System", "S")]

        xs, labels = list(range(len(present))), [ab for _, ab in present]
        for x, (flow, _) in zip(xs, present):
            base = 0.0
            sign = -1.0 if flow == CREDIT else 1.0
            for gr in GROUPS:
                v = g.get((scen, metric, flow, gr), 0.0)
                if not v:
                    continue
                ax.bar(x, sign * v, bottom=base, width=0.72,
                       color=pal.RESOURCE[gr], linewidth=0)
                base += sign * v
            total = sum(g.get((scen, metric, flow, gr), 0.0) for gr in GROUPS)
            up = base >= 0
            ax.annotate(fmt(total) if total else "0", (x, base), ha="center",
                        fontsize=5.0, va="bottom" if up else "top",
                        xytext=(0, 1.5 if up else -1.5),
                        textcoords="offset points", annotation_clip=False)

        # A structurally zero panel otherwise autoscales to a tiny symmetric
        # range (-0.050 ... 0.050) whose wide decimal tick labels collide with
        # the row's axis title. Pin it to a single zero tick instead.
        if not any(g.get((scen, metric, f, gr), 0.0)
                   for f, _ in present for gr in GROUPS):
            ax.set_ylim(0, 1)
            ax.set_yticks([0])

        ax.axhline(0, color="black", lw=0.5)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, fontsize=5)
        ax.tick_params(axis="y", labelsize=5.0)
        # no x tick marks: the flow letters label the bars directly, and the
        # marks would otherwise float against a hidden bottom spine
        ax.tick_params(axis="x", length=0, pad=2)
        ax.set_xlim(-0.65, len(present) - 0.35)
        ax.spines["bottom"].set_visible(False)
        # headroom so the printed totals clear the bar ends and each other
        ax.margins(y=0.22)
        if col == 0:
            ax.set_ylabel(ROW_LABEL[metric], fontsize=5.6)
        if row == 0:
            ax.set_title(SHORT.get(scen, scen), fontsize=6, pad=9)
        # one letter per panel, in reading order: a caption cannot reference a
        # panel that has no label, and this figure has 24 of them
        panel_label(fig, ax, LETTERS[row * len(SCEN) + col], dx=0.030,
                    dy=0.004)

handles = [plt.Rectangle((0, 0), 1, 1, color=pal.RESOURCE[gr]) for gr in GROUPS]
fig.legend(handles, GROUPS, loc="lower center", ncol=4, fontsize=5.4,
           frameon=False, bbox_to_anchor=(0.5, 0.005), handlelength=1.1,
           columnspacing=1.4, handletextpad=0.5)

save(fig, "Figure2_FOM_by_scenario")
print("  flows drawn: S=System, I=Input, P=Process Operations, "
      "W=Waste, O=useful Output (credit, drawn downward)")
