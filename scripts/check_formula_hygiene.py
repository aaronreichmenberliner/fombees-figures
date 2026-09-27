"""Scan every formula for the defect classes found in draft 8 review.

Three of the four workbook defects found by review were of two mechanical
classes that a machine can find faster and more reliably than a person:

  A. the same product term appearing twice in one sum
     (GENE GUN!B194 charged cold storage twice, 43.63 kgeq;
      VIRAL!B167 charged water twice)
  B. an arithmetic formula referencing a cell that is empty or holds text
     (FLOWN!B56 summed B5, a blank in the prose block, instead of B52;
      AGRO!B275 multiplied an empty C263 by the crew-time factor)

Reported rather than fixed: repairing the workbook is the co-author's call.
"""
from __future__ import annotations

import re
import sys
from collections import Counter

import openpyxl

from fombees_paths import workbook

# a parenthesised product such as (C183*E189)
TERM = re.compile(r"\(([A-Z]{1,3}\d{1,4}\s*\*\s*[A-Z]{1,3}\d{1,4})\)")
# a bare cell reference on this sheet
REF = re.compile(r"(?<![A-Z0-9!$:])(\$?[A-Z]{1,3}\$?\d{1,4})(?![\(\d:])")


def norm(term: str) -> str:
    return term.replace(" ", "").replace("$", "")


def severity(formula: str) -> str:
    """An ESM aggregation is a sum of products; a unit conversion is not.

    A blank operand inside an ESM roll-up silently drops a cost term. The same
    blank inside a /1000 unit conversion on an unused input row is noise.
    """
    return "HIGH" if ("+" in formula and "*" in formula) or \
        formula.count("+") >= 3 else "low"


def run() -> list[str]:
    F = openpyxl.load_workbook(workbook())
    V = openpyxl.load_workbook(workbook(), data_only=True)
    findings = []

    for name in F.sheetnames:
        sf, sv = F[name], V[name]
        for row in sf.iter_rows():
            for cell in row:
                f = cell.value
                if not isinstance(f, str) or not f.startswith("="):
                    continue

                # -- A. duplicated product terms
                terms = [norm(t) for t in TERM.findall(f)]
                for term, n in Counter(terms).items():
                    if n > 1:
                        a, b = term.split("*")
                        va, vb = sv[a].value, sv[b].value
                        amount = ((va or 0) * (vb or 0)) if all(
                            isinstance(x, (int, float)) for x in (va, vb)) else None
                        extra = f" worth {amount * (n-1):,.4f} each extra" if amount else ""
                        findings.append((
                            "HIGH",
                            f"{name}!{cell.coordinate}: ({term}) appears {n}x"
                            f"{extra}\n           {f[:96]}"))

                # -- B. arithmetic on an empty or text cell
                if "!" in f:
                    continue          # skip cross-sheet, refs resolve elsewhere
                for ref in set(REF.findall(f)):
                    ref = ref.replace("$", "")
                    if ref == cell.coordinate:
                        continue
                    try:
                        v = sv[ref].value
                    except (ValueError, KeyError):
                        continue
                    if v is None or isinstance(v, str):
                        kind = "empty" if v is None else f"text {v[:26]!r}"
                        findings.append((
                            severity(f),
                            f"{name}!{cell.coordinate}: references {ref} which "
                            f"is {kind}\n           {f[:96]}"))
    return findings


if __name__ == "__main__":
    fs = run()
    high = [x for sev, x in fs if sev == "HIGH"]
    low = [x for sev, x in fs if sev != "HIGH"]
    if not fs:
        print("  no duplicated terms and no arithmetic on empty cells")
    else:
        print(f"  {len(high)} finding(s) inside ESM aggregation formulas:")
        for x in high:
            print(f"    {x}")
        print(f"\n  {len(low)} in unit conversions on blank input rows "
              f"(no cost term dropped):")
        for x in low:
            print(f"    {x.splitlines()[0]}")
    # reported, not enforced: these are the co-author's to repair
    sys.exit(0)
