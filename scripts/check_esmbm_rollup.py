"""Cross-check summed ESM_BM against each sheet's own roll-up row.

This exists because a label mismatch once made the summation silently drop a
row - FLOWN spells its waste row "Waste outputs" where the others write "Waste
process outputs" - and 124 kgeq went missing through five published figures. A
dropped row cannot hide from the sheet's own total, so compare against it.

Separately, several roll-up formulas in the workbook omit a term. Those are
asserted at their exact known values so this fails if one is repaired (in which
case update the table) or if a new one appears.
"""
from __future__ import annotations

import sys

import re

import openpyxl

import read_esmbm as R
from fombees_paths import workbook

# scenario -> (row label carrying the authoritative total, expected gap)
# gap = summed - sheet's own total; non-zero means the sheet's formula is wrong.
ROLLUP = {
    "FLOWN":              ("ESMBM (kgeq)",               0.0),
    "TRANSGENIC-LETTUCE": ("ESMBM (kgeq)",               0.0),
    "TRANSGENIC-TOBACCO": ("ESMBM (kgeq)",               0.0),
    "AGRO":               ("Total Overall ESMBM (kgeq)", 0.0),
    "VIRAL":              ("Total Overall ESMBM (kgeq)", 0.0),
    # GENE GUN's label omits the "BM" that every other sheet carries. An
    # earlier version searched for "ESMBM" and therefore concluded this sheet
    # had no roll-up at all, exempting the largest scenario in the study from
    # the only independent cross-check in the pipeline.
    "GENE GUN":           ("Total Overall ESM (kgeq)",   0.0),
}

# Sheets whose ESM_BM is reported in parts as well as in total. Until these
# were repaired, three of the part formulas omitted their Process-Operations
# term, so the parts silently failed to add up to the whole and anyone checking
# the sheet by hand got the pre-correction number. Asserted positively now
# rather than catalogued as known-bad.
PARTS = {
    "GENE GUN": (["B80", "B197"], "B208"),
    "AGRO":     (["B74", "B278"], "B289"),
    "VIRAL":    (["B74", "B170"], "B181"),
}

TOL = 0.01


def run() -> list[str]:
    F = openpyxl.load_workbook(workbook())
    V = openpyxl.load_workbook(workbook(), data_only=True)
    computed, bad = R.read(), []

    print("  totals:")
    for scen, (label, expected_gap) in ROLLUP.items():
        sheet, own = V[scen], None
        for r in range(1, sheet.max_row + 1):
            a = sheet.cell(r, 1).value
            if a and str(a).strip() == label:
                own = sheet.cell(r, 2).value
                break
        if own is None:
            bad.append(f"{scen}: no row labelled {label!r}")
            continue
        gap = computed[scen]["ESM_BM"] - own
        ok = abs(gap - expected_gap) < TOL
        print(f"    {'ok ' if ok else 'BAD'} {scen:<20} summed "
              f"{computed[scen]['ESM_BM']:>11,.2f}  sheet {own:>11,.2f}  "
              f"gap {gap:>8,.2f}")
        if not ok:
            bad.append(f"{scen}: gap {gap:,.2f}, expected {expected_gap:,.2f}")
    print("  parts sum to the whole:")
    for scen, (part_cells, total_cell) in PARTS.items():
        sheet = V[scen]
        parts = [sheet[c].value for c in part_cells]
        total = sheet[total_cell].value
        if any(p is None for p in parts) or total is None:
            bad.append(f"{scen}: a part or total cell is empty")
            continue
        got, ok = sum(parts), abs(sum(parts) - total) < TOL
        print(f"    {'ok ' if ok else 'BAD'} {scen:<20} "
              + " + ".join(f"{c} {p:,.2f}" for c, p in zip(part_cells, parts))
              + f"  =  {got:>12,.2f}   {total_cell} {total:>12,.2f}")
        if not ok:
            bad.append(f"{scen}: parts sum to {got:,.2f} but {total_cell} "
                       f"says {total:,.2f}")

    # every ESM_BM roll-up must carry all five category terms
    print("  every roll-up carries all five category rows:")
    for scen in R.SCEN:
        sheet = F[scen]
        for r in range(1, sheet.max_row + 1):
            lab = sheet.cell(r, 1).value
            if not (isinstance(lab, str) and "ESM" in lab and "kgeq" in lab):
                continue
            f = str(sheet.cell(r, 2).value or "")
            refs = set(re.findall(r"B(\d+)", f))
            base = min(int(x) for x in refs) if refs else None
            want = {str(base + i) for i in range(5)} if base else set()
            ok = want <= refs
            print(f"    {'ok ' if ok else 'BAD'} {scen:<20} B{r:<4} {f}")
            if not ok:
                bad.append(f"{scen}!B{r} omits {sorted(want - refs)}: {f}")
    return bad


if __name__ == "__main__":
    fails = run()
    for f in fails:
        print(f"  FAIL {f}")
    print("  all roll-ups reconcile" if not fails else f"  {len(fails)} failed")
    sys.exit(1 if fails else 0)
