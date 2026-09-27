"""Confirm every rendered figure traces to the CURRENT workbook.

Three separate ways a figure can drift away from the spreadsheet it claims to
represent, each checked here:

 1. The pipeline reads the wrong file. Resolved path is printed so it can be
    read at a glance.
 2. A derived cache was built from a different workbook. This bit us: the
    sensitivity cache was copied into a new working directory, which made it
    NEWER than the workbook while its contents still came from the previous
    one. A modification-time test passes in that situation; only the content
    hash catches it.
 3. The figures on disk predate the last render. Compared against the source
    the pipeline actually read.
"""
from __future__ import annotations

import hashlib
import json
import sys

import openpyxl

from fombees_paths import figures_dir, workbook
from read_esmbm import read
from sensitivity import CACHE, workbook_hash

# the cell on each sheet holding that scenario's own ESM_BM total
TOTAL_CELL = {
    "FLOWN": ("FLOWN", "B56"),
    "TRANSGENIC-LETTUCE": ("TRANSGENIC-LETTUCE", "B80"),
    "TRANSGENIC-TOBACCO": ("TRANSGENIC-TOBACCO", "B74"),
    "GENE GUN": ("GENE GUN", "B208"),
    "AGRO": ("AGRO", "B289"),
    "VIRAL": ("VIRAL", "B181"),
}
TOL = 0.01


def run() -> list[str]:
    bad = []
    wb = workbook()
    digest = workbook_hash()
    print(f"  source: {wb.name}")
    print(f"  sha256[:16]: {digest}")

    V = openpyxl.load_workbook(wb, data_only=True)
    r = read()
    print("\n  pipeline totals against each sheet's own total cell:")
    for scen, (sheet, cell) in TOTAL_CELL.items():
        got, want = r[scen]["ESM_BM"], V[sheet][cell].value
        ok = want is not None and abs(got - want) < TOL
        print(f"    {'ok ' if ok else 'BAD'} {scen:<20} pipeline "
              f"{got:>12,.4f}   {sheet}!{cell} {want:>12,.4f}")
        if not ok:
            bad.append(f"{scen}: pipeline {got:,.4f} != {sheet}!{cell} {want}")

    print("\n  derived caches:")
    if not CACHE.exists():
        print("    -- sensitivity cache absent; it will be derived on demand")
    else:
        c = json.loads(CACHE.read_text())
        stamp = c.get("workbook_sha256_16", "unstamped")
        ok = stamp == digest
        print(f"    {'ok ' if ok else 'BAD'} sensitivity.json stamped "
              f"{stamp} ({c.get('workbook', '?')})")
        if not ok:
            bad.append(f"sensitivity cache built from {stamp}, not {digest}")
        else:
            for scen, base in c["base"].items():
                s, cell = TOTAL_CELL[scen]
                if abs(base - V[s][cell].value) > TOL:
                    bad.append(f"sensitivity base {scen} disagrees with "
                               f"{s}!{cell}")

    print("\n  figures are newer than the workbook they were rendered from:")
    wb_t = wb.stat().st_mtime
    for f in sorted(figures_dir().glob("Figure*.pdf")):
        ok = f.stat().st_mtime > wb_t
        print(f"    {'ok ' if ok else 'BAD'} {f.name}")
        if not ok:
            bad.append(f"{f.name} predates the workbook")
    return bad


if __name__ == "__main__":
    fails = run()
    for f in fails:
        print(f"  FAIL {f}")
    print("\n  every figure traces to the current workbook" if not fails
          else f"\n  {len(fails)} provenance failure(s)")
    sys.exit(1 if fails else 0)
