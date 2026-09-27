"""Nature figure specification, applied once for every figure script.

Two constraints drive the odd-looking helpers here:

 - All text must sit between 5 and 7 pt at final printed size. matplotlib
   renders mathtext super/subscripts at 0.7x the base size, so a 7 pt label
   with an exponent puts the exponent at 4.9 pt - unreachable within the
   ceiling. Exponents are therefore written with UNICODE superscripts (m3 as
   "m\u00b3"), which are ordinary glyphs at the full point size rather than
   mathtext. Helvetica carries U+00B2, U+00B3, U+00B9 and U+207B, so these
   embed like any other character. plain_log() likewise avoids mathtext for
   decade labels.
 - Text must stay as text in the PDF, never outlines, so fonttype is 42.
"""
from __future__ import annotations

import json
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from fombees_paths import figures_dir

MM = 1 / 25.4

mpl.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 6,
    "axes.labelsize": 6,
    "axes.titlesize": 6,
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
    "legend.fontsize": 5,
    "axes.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelpad": 2,
    "lines.linewidth": 0.9,
    "lines.markersize": 3,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.major.size": 2,
    "ytick.major.size": 2,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "axes.grid": False,
})

SUP = {"3": "\u00b3", "2": "\u00b2", "1": "\u00b9", "-": "\u207b"}

# Subscripted symbols, matching how the manuscript typesets them.
#
# These have to go through mathtext: Unicode has no subscript B or M, so
# "ESM_BM" cannot be written with ordinary glyphs the way m3 can. matplotlib
# renders a mathtext subscript at exactly 0.700 of the base size (measured, not
# assumed), so a 6 pt label would put the subscript at 4.2 pt, well under the
# 5 pt floor. SUBSCRIPT_PT is therefore the smallest base that keeps the
# subscript legal: 7.2 x 0.700 = 5.04 pt.
#
# Axis titles that carry no subscript are set to the same size within a figure,
# so the type does not visibly change from one axis to the next.
# \mathrm keeps the subscript upright. Bare mathtext letters are set italic,
# because mathtext reads them as variables; BM and eq are labels, not
# variables, and the style requires units and qualifiers upright.
ESMBM = "ESM$_\\mathrm{BM}$"
KGEQ = "kg$_\\mathrm{eq}$"
SUBSCRIPT_PT = 7.2


def sup(unit: str) -> str:
    """Render an exponent with unicode superscripts, never mathtext."""
    return "".join(SUP.get(c, c) for c in unit)


METRIC_LABEL = {
    "mass": "mass (kg per CM)",
    "volume": "volume (m\u00b3 per CM)",
    "power": "power (kW per CM)",
    "crew_time": "crew time (CM-h per CM)",
}


def fmt(v: float) -> str:
    """Compact number for printing inside a panel."""
    a = abs(v)
    if a == 0:
        return "0"
    if a >= 1000:
        return f"{v:,.0f}"
    if a >= 100:
        return f"{v:.0f}"
    if a >= 10:
        return f"{v:.1f}"
    if a >= 1:
        return f"{v:.2f}"
    if a >= 0.01:
        return f"{v:.3f}"
    return f"{v:.2e}".replace("e-0", "e-")


def plain_log(ax, axis: str = "x") -> None:
    """Label a log axis as plain decimals, never as 10^n mathtext."""
    def f(v, _pos):
        if v <= 0:
            return ""
        if v >= 1000:
            return f"{v:,.0f}"
        if v >= 1:
            return f"{v:g}"
        return f"{v:g}"
    target = ax.xaxis if axis == "x" else ax.yaxis
    target.set_major_formatter(FuncFormatter(f))


# mathtext -> unicode, so exponents keep the full point size
_SUB = {"CO$_2$": "CO\u2082", "O$_2$": "O\u2082",
        "m$^3$": "m\u00b3", "$^{-1}$": "\u207b\u00b9"}


def no_mathtext(s: str) -> str:
    """Strip mathtext so nothing renders below the 5 pt floor."""
    for a, b in _SUB.items():
        s = s.replace(a, b)
    return re.sub(r"\$([^$]*)\$", r"\1", s)


def panel_label(fig, ax, letter: str, dx: float = 0.13, dy: float = 0.010) -> None:
    bb = ax.get_position()
    fig.text(bb.x0 - dx, bb.y1 + dy, letter, fontsize=8, fontweight="bold",
             va="bottom", ha="left")


def stagger_labels(ax, items, x, min_gap=0.055, **kw):
    """Annotate curve ends, pushing apart labels that would overlap.

    Curves that converge (FLOWN and VIRAL, for instance) would otherwise print
    their names on top of each other. Positions are resolved in axes-fraction
    space so the minimum gap means the same thing on a log axis as on a linear
    one.

    items: iterable of (data_y, text, colour), any order.
    """
    import numpy as np

    lo, hi = ax.get_ylim()

    def to_frac(v):
        if ax.get_yscale() == "log":
            return (np.log10(v) - np.log10(lo)) / (np.log10(hi) - np.log10(lo))
        return (v - lo) / (hi - lo)

    rows = sorted(((to_frac(v), text, col) for v, text, col in items),
                  key=lambda t: t[0])
    fracs = [f for f, _, _ in rows]
    # single upward pass, then clamp back under the top edge
    for i in range(1, len(fracs)):
        if fracs[i] - fracs[i - 1] < min_gap:
            fracs[i] = fracs[i - 1] + min_gap
    overflow = fracs[-1] - 1.0
    if overflow > 0:
        fracs = [f - overflow for f in fracs]
    for f, (_, text, col) in zip(fracs, rows):
        ax.annotate(text, (x, f), xycoords=("data", "axes fraction"),
                    color=col, ha="left", va="center", annotation_clip=False,
                    xytext=(2.5, 0), textcoords="offset points", **kw)


def save(fig, stem: str) -> None:
    """Write the figure, and record its tick labels next to it.

    The tick labels are recorded because the printed-number check reads the PDF
    text layer, where an axis tick is indistinguishable from a data label. Ticks
    are generated by matplotlib from the axis scale rather than from the data,
    so they are not a correctness risk - but they must be excluded by identity,
    not by loosening the tolerance, which would blind the check to real errors.
    """
    out = figures_dir()
    fig.canvas.draw()                      # ticks are not final until drawn
    ticks = set()
    for ax in fig.axes:
        for lab in (*ax.get_xticklabels(), *ax.get_yticklabels()):
            t = lab.get_text().strip()
            if t:
                ticks.add(t)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{stem}.{ext}")
    (out / f"{stem}.ticks.json").write_text(json.dumps(sorted(ticks), indent=1))
    plt.close(fig)
    print(f"  wrote figures/{stem}.pdf and .png ({len(ticks)} tick labels)")


def audit_text_sizes(fig, floor: float = 5.0, ceiling: float = 8.0) -> list[str]:
    """Return every text artist whose effective size falls outside the spec.

    Mathtext sub/superscripts render at 0.7x, so a nominal 7 pt with an exponent
    is really 4.9 pt. Those are reported at their effective size, not nominal.
    """
    bad = []
    for t in fig.findobj(mpl.text.Text):
        s = t.get_text()
        if not s.strip():
            continue
        size = t.get_fontsize()
        eff = size * 0.7 if "$" in s else size
        if eff < floor - 1e-9 or eff > ceiling + 1e-9:
            bad.append(f"{eff:.2f} pt  {s[:40]!r}")
    return bad
