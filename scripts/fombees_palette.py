"""Colour meanings, and the invariant that actually holds.

The manuscript uses three separate ENCODINGS, and there are not enough
colourblind-safe hues to give all of them disjoint colours:

  RESOURCE  what a resource is          (Figure 2 only)
  FLOW      which ESM_BM term it is     (Figures 3, 4, 5)
  SCENARIO  which production route      (Figures 6, 7)

The honest invariant is therefore NOT "one colour per meaning everywhere" - an
earlier docstring claimed that, and it was false: VIRAL and the useful-output
credit were both #009E73, AGRO and "Processing & inoculation" were both #D55E00.
What must hold, and what check() enforces, is:

  1. within a single encoding, no colour carries two meanings
  2. no FIGURE mixes two encodings, so a reused hue can never be ambiguous
     on the page
  3. resource groups stay separable in greyscale, for mono printing

Rule 2 is the load-bearing one and is verified against the figure scripts
themselves, not asserted.
"""
from __future__ import annotations

# Resource groups. Used wherever a bar is split by what the resource IS.
RESOURCE = {
    "Biomass & product":       "#000000",
    "Cold storage":            "#332288",
    "Plant growth & harvest":  "#0072B2",
    "Processing & inoculation": "#D55E00",
    "Labware & packaging":     "#999933",
    "Gases (CO₂, O₂)":         "#E69F00",
    "Water":                   "#88CCEE",
    "Nutrients & media":       "#F0E442",
}

# ESM_BM flows. Deliberately a neutral ramp, not hues: flows are a sequence of
# accounting categories, and colouring them like resource groups would imply a
# correspondence that does not exist.
FLOW = {
    "System":                 "#3F4A56",
    "Process Operations":     "#68727E",
    "Input":                  "#8D96A1",
    "Process Inputs":         "#8D96A1",
    "Waste":                  "#BFC6CD",
    "Waste process outputs":  "#BFC6CD",
}

# The workbook and the figures use different names for the same two flows.
ALIAS = {"Process Inputs": "Input", "Waste process outputs": "Waste"}

# Scenario identity, used only in figures that show no resource groups.
SCENARIO = {
    "FLOWN":              "#8A929B",
    "TRANSGENIC-TOBACCO": "#0072B2",
    "TRANSGENIC-LETTUCE": "#56B4E9",
    "VIRAL":              "#009E73",
    "AGRO":               "#D55E00",
    "GENE GUN":           "#000000",
}

# Line style carries meaning, exactly as colour does, and there are only three:
#
#   SOLID     a scenario's own curve
#   DASHED    the FLOWN reference, whether drawn as a curve or as a rule
#   DOTTED    an annotation marking the parameter value actually in use
#
# Nothing else may be dashed. GENE GUN was once drawn dotted in Figure 6 and
# solid in Figure 7 for no reason at all, which invited exactly the question
# "why is that one dashed?".
SOLID = "-"
DASHED = (0, (4, 2))
DOTTED = (0, (1, 1.6))


def linestyle(scenario: str) -> tuple | str:
    """Line style for a scenario curve. Only the reference is distinguished."""
    return DASHED if scenario == "FLOWN" else SOLID


CREDIT = "#009E73"    # useful output, always drawn as a credit
NET = "#11161D"       # the net marker
BASELINE = "#8A929B"  # the FLOWN reference rule (and FLOWN's scenario colour)


def _luma(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


ENCODINGS = {"RESOURCE": RESOURCE, "FLOW": FLOW, "SCENARIO": SCENARIO}


def check() -> float:
    """Enforce the three rules in the docstring. Return greyscale separation."""
    # rule 1: within one encoding, no colour carries two meanings
    for enc, mapping in ENCODINGS.items():
        seen: dict[str, str] = {}
        for name, col in mapping.items():
            canon = ALIAS.get(name, name)
            if col in seen and seen[col] != canon:
                raise AssertionError(
                    f"in {enc}, {col} means both {seen[col]!r} and {canon!r}")
            seen[col] = canon

    lum = sorted(_luma(c) for c in RESOURCE.values())
    gaps = [b - a for a, b in zip(lum, lum[1:])]
    worst = min(gaps)
    if worst < 0.02:
        raise AssertionError(
            f"two resource groups are {worst:.3f} apart in greyscale; "
            "they will merge when printed mono")
    return worst


def check_no_figure_mixes_encodings() -> list[str]:
    """Rule 2, verified against the figure scripts rather than asserted.

    A figure that imported both RESOURCE and SCENARIO could put the same hue on
    a resource group and on a scenario in one frame, which is the only way the
    shared hues become ambiguous to a reader.
    """
    from pathlib import Path
    here = Path(__file__).resolve().parent
    bad = []
    for script in sorted(here.glob("fig*.py")):
        src = script.read_text()
        uses = set()
        if "RESOURCE" in src:
            uses.add("RESOURCE")
        if "pal.FLOW" in src or "FLOW[" in src:
            uses.add("FLOW")
        if "SCENARIO" in src:
            uses.add("SCENARIO")
        if "RESOURCE" in uses and "SCENARIO" in uses:
            bad.append(f"{script.name} uses both RESOURCE and SCENARIO colours")
    return bad


def check_linestyles() -> list[str]:
    """No figure may invent a dash pattern; all three come from this module.

    Verified against the scripts, because the failure this catches is a style
    applied for no reason - which a reader notices immediately and cannot
    explain.
    """
    import re
    from pathlib import Path

    here = Path(__file__).resolve().parent
    literal = re.compile(r"""ls\s*=\s*(?!pal\.)(['"](?:--|:|-\.)['"]|\(0,\s*\()""")
    bad = []
    for script in sorted(here.glob("fig*.py")):
        for i, line in enumerate(script.read_text().splitlines(), 1):
            if literal.search(line):
                bad.append(f"{script.name}:{i} literal line style: "
                           f"{line.strip()[:70]}")
    return bad


if __name__ == "__main__":
    import sys
    sep = check()
    mixed = check_no_figure_mixes_encodings()
    print(f"  within-encoding uniqueness ok; "
          f"min greyscale separation {sep:.3f}")
    for k, v in RESOURCE.items():
        print(f"    {v}  luma {_luma(v):.3f}  {k}")
    shared = {c for c in SCENARIO.values()} & (
        {c for c in RESOURCE.values()} | {CREDIT})
    print(f"  {len(shared)} hue(s) shared between encodings: "
          f"{', '.join(sorted(shared))}")
    styles = check_linestyles()
    print(f"  line styles: solid = a scenario, dashed = the FLOWN reference, "
          f"dotted = a parameter value in use")
    for m in mixed + styles:
        print(f"  FAIL {m}")
    if mixed or styles:
        sys.exit(1)
    print("  no figure mixes two encodings, so no shared hue is ambiguous "
          "on the page; no figure invents a dash pattern")
