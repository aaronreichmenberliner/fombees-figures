"""Every scenario input must READ from the Assumptions tab, not hard-code it.

This is the co-author's stated requirement - "I'd like them all to be linked so
the user can just change that value and everything propagates through" - turned
into a test.

It exists because VIRAL!B7 hard-coded its expression level at 300 where the
four sibling sheets referenced the Assumptions tab. Nothing was numerically
wrong: 300 is also what the Assumptions tab said. But the titer did not
propagate, so VIRAL sat flat across every expression-level sensitivity, and the
figure showed a straight line that looked like a result and was not one.

NOTE: the dose lives at Assumptions!B8. Assumptions!B5 is CREW SIZE, and is
already the divisor in dozens of shared-equipment formulas, so nothing may be
repointed at it.
"""
from __future__ import annotations

import sys

import openpyxl

from fombees_paths import workbook

DOSE_CELL = "B8"          # Assumptions!B8, 'Base case dose'
CREW_CELL = "B5"          # Assumptions!B5, 'Crew size' - NOT the dose

# scenario -> (cell taking the dose, cell taking the expression level)
# The duplicate dose row was deleted upstream, so the titer moved from B7 to
# B6 on every plant sheet.
LINKS = {
    "FLOWN":              ("B13", None),
    "TRANSGENIC-LETTUCE": ("B5", "B6"),
    "TRANSGENIC-TOBACCO": ("B5", "B6"),
    "GENE GUN":           ("B5", "B6"),
    "AGRO":               ("B5", "B6"),
    "VIRAL":              ("B5", "B6"),
}


def run() -> list[str]:
    F = openpyxl.load_workbook(workbook())
    V = openpyxl.load_workbook(workbook(), data_only=True)
    A = V["Assumptions"]
    bad = []

    print(f"  Assumptions!{DOSE_CELL} '{A[DOSE_CELL].offset(column=-1).value}'"
          f" = {A[DOSE_CELL].value}   <- the dose")
    print(f"  Assumptions!{CREW_CELL} '{A[CREW_CELL].offset(column=-1).value}'"
          f" = {A[CREW_CELL].value}   <- NOT the dose; do not repoint here")

    for scen, (dose_cell, expr_cell) in LINKS.items():
        for kind, cell in (("dose", dose_cell), ("titer", expr_cell)):
            if cell is None:
                continue
            f = F[scen][cell].value
            linked = isinstance(f, str) and f.startswith("=") \
                and "Assumptions!" in f
            print(f"    {'ok ' if linked else 'BAD'} {scen:<20} {cell:<4} "
                  f"{kind:<6} {str(f)[:34]!r}")
            if not linked:
                bad.append(f"{scen}!{cell} ({kind}) is hard-coded as {f!r}; it "
                           f"must reference the Assumptions tab or it will not "
                           f"propagate")
    return bad


if __name__ == "__main__":
    fails = run()
    for f in fails:
        print(f"  FAIL {f}")
    print("  every dose and titer reads from the Assumptions tab" if not fails
          else f"  {len(fails)} unlinked input(s)")
    sys.exit(1 if fails else 0)
