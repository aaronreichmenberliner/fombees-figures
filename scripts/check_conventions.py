"""Verify the ESM_BM conventions are applied identically on every sheet.

The FOM Graphs block and the ESM category rows are two accounts of one system
and they do NOT agree numerically - by up to 46% on some scenarios. That is not
an error. Two stated conventions explain the whole difference:

  1. Water is priced through W_eq alone and is excluded from the mass and
     volume terms, so it is not counted twice.
  2. Waste carries mass only, priced by WS_eq; waste volume is not charged.

An adversarial review reconstructed ESM from the FOM block without applying
these and concluded the metric was understated. Encoding them here means the
next reader gets the answer instead of the alarm - and, more usefully, that a
sheet which silently stops following a convention fails a check.

Convention 2 is a real limitation, not merely bookkeeping: GENE GUN's 7.78 m3
of waste volume is about 617 kgeq the metric never prices. That belongs in the
manuscript as a caveat, and is reported below.
"""
from __future__ import annotations

import sys

import openpyxl

from fombees_paths import workbook
from load import by_group, totals
from read_esmbm import read

VEQ, WSEQ = 79.3, 0.93
# Located by label: the plant sheets shifted up a row when the duplicate dose
# row was deleted, and a fixed row number then reads its neighbour in silence.
WASTE_LABELS = ("Waste outputs", "Waste process outputs")


def _waste_row(sheet) -> int:
    for r in range(1, sheet.max_row + 1):
        a = sheet.cell(r, 1).value
        if isinstance(a, str) and a.strip() in WASTE_LABELS:
            return r
    raise LookupError(f"{sheet.title}: no waste category row")


WASTE_SHEETS = ["FLOWN", "TRANSGENIC-LETTUCE", "TRANSGENIC-TOBACCO"]
TOL = 0.01


def run() -> list[str]:
    V = openpyxl.load_workbook(workbook(), data_only=True)
    tot, g, r = totals(), by_group(), read()
    bad = []

    print("  convention 2 - waste priced on mass alone, at WS_eq:")
    for s in WASTE_SHEETS:
        row = _waste_row(V[s])
        mass = tot.get((s, "mass", "Waste"), 0.0)
        want, got = mass * WSEQ, V[s].cell(row, 2).value
        ok = abs(want - got) < TOL
        print(f"    {'ok ' if ok else 'BAD'} {s:<20} {mass:>9,.3f} kg x "
              f"{WSEQ} = {want:>9,.3f}   sheet {got:>9,.3f}")
        if not ok:
            bad.append(f"{s}: waste ESM {got:,.3f} != mass x WS_eq {want:,.3f}")

    print("\n  convention 1 - water excluded from the volume term:")
    for s in ("TRANSGENIC-LETTUCE", "TRANSGENIC-TOBACCO"):
        wv = g.get((s, "volume", "Input", "Water"), 0.0)
        print(f"    -- {s:<20} {wv:>8.4f} m3 of input water volume, worth "
              f"{wv * VEQ:>8,.2f} kgeq, deliberately not charged")

    print("\n  unpriced waste volume, for the manuscript's limitations "
          "paragraph:")
    for s, v in sorted(r.items(), key=lambda kv: -tot.get((kv[0], "volume", "Waste"), 0.0)):
        wv = tot.get((s, "volume", "Waste"), 0.0)
        if wv:
            print(f"    -- {s:<20} {wv:>8.4f} m3 = {wv * VEQ:>8,.1f} kgeq "
                  f"({100 * wv * VEQ / v['ESM_BM']:>5.1f}% of its ESMBM)")
    return bad


if __name__ == "__main__":
    fails = run()
    print("\n  conventions applied consistently" if not fails
          else f"\n  {len(fails)} convention violation(s)")
    for f in fails:
        print(f"  FAIL {f}")
    sys.exit(1 if fails else 0)
