"""Derive sensitivities by recomputing the workbook, not by approximating it.

An earlier version of Figure 6b drew expression-level curves from hand-written
"growth share" constants that were not derivable from any cell - they were
invented, and because that panel prints no numbers, nothing could catch it.

This recomputes the actual workbook with the input perturbed, which is the only
honest way to get these curves: plant counts pass through ROUNDUP and equipment
counts through CEILING, so the response is genuinely step-wise and no smooth
analytic form reproduces it.

Results are cached to data/sensitivity.json, stamped with a hash of the
workbook they came from. The cache is rejected if that hash does not match the
current workbook.

A modification-time check is not enough and would have failed here: the cache
was copied into a new working directory, which made it NEWER than the workbook
while its contents still came from the previous one. Only the contents can
answer whether a cache is current.
"""
from __future__ import annotations

import hashlib
import json
import re

from fombees_paths import ROOT, workbook

CACHE = ROOT / "data" / "sensitivity.json"

SCEN_TOTAL = {                     # sheet -> cell holding that scenario's ESM_BM
    "FLOWN": "B56",
    "TRANSGENIC-LETTUCE": "B80",
    "TRANSGENIC-TOBACCO": "B74",
    "GENE GUN": "B208",
    "AGRO": "B289",
    "VIRAL": "B181",
}
EXPRESSION_CELL = {                # Assumptions cell holding each titer
    "TRANSGENIC-LETTUCE": "C17",
    "TRANSGENIC-TOBACCO": "C18",
    "GENE GUN": "C19",
    "AGRO": "C20",
    "VIRAL": "C21",
}
TEQ_CELL = "H13"
MULTIPLIERS = [0.1, 0.15, 0.25, 0.4, 0.6, 0.8, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0]
TEQ_VALUES = [0.0, 0.25, 0.5, 0.75, 0.94, 1.25, 1.75, 2.25, 2.75, 3.39, 4.0]


def workbook_hash() -> str:
    return hashlib.sha256(workbook().read_bytes()).hexdigest()[:16]


def _model():
    import formulas
    return formulas.ExcelModel().loads(str(workbook())).finish()


def _key(sol, sheet: str, cell: str) -> str:
    pat = re.compile(rf"\]{re.escape(sheet)}'!{cell}$", re.I)
    for k in sol:
        if pat.search(k):
            return k
    raise KeyError(f"{sheet}!{cell} not found in the computed model")


def _val(sol, key: str) -> float:
    return float(sol[key].value[0, 0])


def derive() -> dict:
    xl = _model()
    base = xl.calculate()
    tgt = {s: _key(base, s, c) for s, c in SCEN_TOTAL.items()}
    expr_in = {s: _key(base, "ASSUMPTIONS", c)
               for s, c in EXPRESSION_CELL.items()}
    teq_in = _key(base, "ASSUMPTIONS", TEQ_CELL)
    base_expr = {s: _val(base, expr_in[s]) for s in expr_in}

    out = {
        "workbook": workbook().name,
        "workbook_sha256_16": workbook_hash(),
        "base": {s: _val(base, tgt[s]) for s in tgt},
        "base_expression": base_expr,
        "expression": {"multipliers": MULTIPLIERS, "curves": {}},
        "teq": {"values": TEQ_VALUES, "curves": {}},
    }

    # one recompute per multiplier: the five titers feed five different sheets,
    # so perturbing them together still yields five independent curves
    for m in MULTIPLIERS:
        sol = xl.calculate(
            inputs={expr_in[s]: base_expr[s] * m for s in expr_in})
        for s in EXPRESSION_CELL:
            out["expression"]["curves"].setdefault(s, []).append(
                _val(sol, tgt[s]))
        print(f"    expression x{m:<5} "
              + "  ".join(f"{s[:9]} {_val(sol, tgt[s]):>9,.0f}"
                          for s in EXPRESSION_CELL))

    for t in TEQ_VALUES:
        sol = xl.calculate(inputs={teq_in: t})
        for s in SCEN_TOTAL:
            out["teq"]["curves"].setdefault(s, []).append(_val(sol, tgt[s]))
        print(f"    T_eq {t:<5} "
              + "  ".join(f"{s[:7]} {_val(sol, tgt[s]):>9,.0f}"
                          for s in SCEN_TOTAL))
    return out


def load() -> dict:
    want = workbook_hash()
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if cached.get("workbook_sha256_16") == want:
            return cached
        print(f"  sensitivity cache was built from a different workbook "
              f"({cached.get('workbook_sha256_16', 'unstamped')} vs {want}); "
              f"re-deriving")
    CACHE.parent.mkdir(exist_ok=True)
    data = derive()
    CACHE.write_text(json.dumps(data, indent=1))
    return data


if __name__ == "__main__":
    d = load()
    print(f"\n  cached to {CACHE.relative_to(ROOT)}")
    print(f"  base ESM_BM: "
          + "  ".join(f"{s[:9]} {v:,.0f}" for s, v in d["base"].items()))
