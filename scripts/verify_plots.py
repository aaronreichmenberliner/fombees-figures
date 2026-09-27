"""Check every number printed inside a figure against the model.

Two things this gets right that a naive version does not:

 - Tolerance is set by PRINTED PRECISION, not a relative percentage. An earlier
   version used 2%, and a measurement showed 84% of arbitrary values matched
   something in the candidate pool - the check could barely fail.
 - Adjacent text runs are kept separate. Merging them invents tokens like
   "1762 94" out of "176" and "294" and then matches them to nothing, or worse,
   to something.
"""
from __future__ import annotations

import json
import re
import sys

from pypdf import PdfReader

from extract_fom import CREDIT
from fombees_paths import figures_dir
from load import METRICS, totals
from read_esmbm import read

NUM = re.compile(r"^-?[\d,]+(?:\.\d+)?(?:e-?\d+)?$")


def candidates() -> list[float]:
    """Every quantity a figure is allowed to print."""
    out: list[float] = []
    tot, r = totals(), read()
    for (_s, _m, _f), v in tot.items():
        out.append(v)
    for s, v in r.items():
        gross = v["GROSS"]
        for k, x in v.items():
            if k.startswith("_"):
                continue
            out.append(x)
            if gross:
                out.append(100 * x / gross)
    # percentages of gross for each FOM, and ranks
    for s in r:
        for m in METRICS:
            g = tot.get((s, m, "Gross"), 0.0)
            if g:
                out.append(100 * tot.get((s, m, CREDIT), 0.0) / g)
                for flow in ("System", "Process Operations", "Input", "Waste"):
                    out.append(100 * tot.get((s, m, flow), 0.0) / g)
                out.append(100 * tot[(s, m, "Net")] / g)
    # crew time per CM per day
    for s in r:
        out.append(tot[(s, "crew_time", "Net")] / 602)
    return [float(x) for x in out]


# Values a specific figure is additionally allowed to print. Kept per-figure so
# that a blanket allowance for ranks does not excuse every small integer in
# every other figure - an earlier version extended the pool with range(0, 11)
# globally and, measured, let 70% of arbitrary small integers pass.
EXTRA = {
    "Figure5_ESM_BM_vs_FOM": list(range(1, 7)),          # panel b ranks
    "Figure7_aggregation": list(range(0, 16)),           # ranks and 0-15 counts
    "Figure6_drivers": [24, 0.94],                       # hours in a day, T_eq
    "Figure3_cross_scenario": [0],                       # structural zero
    "Figure2_FOM_by_scenario": [0],                      # structural zeros
}


def tokens(path):
    """(text, page) for every number printed, without merging adjacent runs."""
    found = []
    for page in PdfReader(path).pages:
        parts: list[str] = []
        page.extract_text(visitor_text=lambda t, *_a: parts.append(t))
        for part in parts:
            for tok in re.split(r"[\s%()/]+", part):
                tok = tok.strip().rstrip(".,")
                if tok and NUM.match(tok):
                    found.append(tok)
    return found


def decimals(tok: str) -> int:
    if "e" in tok.lower():
        return 6
    return len(tok.split(".")[1]) if "." in tok else 0


def run() -> list[str]:
    base = candidates()
    bad = []
    for pdf in sorted(figures_dir().glob("Figure*.pdf")):
        toks = tokens(pdf)
        tick_file = pdf.with_suffix("").with_suffix(".ticks.json")
        if not tick_file.exists():
            bad.append(f"{pdf.name}: no tick record; re-run the figure script")
            print(f"  BAD {pdf.name:<42} no tick record")
            continue
        ticks = set(json.loads(tick_file.read_text()))
        pool = base + [float(x) for x in EXTRA.get(pdf.stem, [])]
        misses, skipped = [], 0
        for tok in toks:
            if tok in ticks:
                skipped += 1
                continue
            try:
                v = float(tok.replace(",", ""))
            except ValueError:
                continue
            # the tolerance the printed precision itself implies
            tol = 0.51 * 10 ** (-decimals(tok))
            if not any(abs(v - c) <= tol for c in pool):
                misses.append(tok)
        status = "ok " if not misses else "BAD"
        print(f"  {status} {pdf.name:<42} {len(toks) - skipped:>4} data "
              f"numbers ({skipped} ticks skipped), {len(misses)} unmatched")
        if misses:
            print(f"        unmatched: {', '.join(sorted(set(misses))[:14])}")
            bad.append(f"{pdf.name}: {len(misses)} unmatched")
    return bad


if __name__ == "__main__":
    fails = run()
    print("  every printed number matches the model" if not fails
          else f"  {len(fails)} figure(s) print unmatched numbers")
    sys.exit(1 if fails else 0)
