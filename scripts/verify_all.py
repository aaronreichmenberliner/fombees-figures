"""Run every check. Exit non-zero if any fails.

Ordering matters: the figure scripts run BEFORE the checks that read the
rendered PDFs, or those checks read stale output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PY = sys.executable
HERE = Path(__file__).resolve().parent

FIGURES = ["fig2.py", "fig3.py", "fig4.py", "fig5.py", "fig6.py"]

CHECKS = [
    ("figures trace to the current workbook", "check_sheet_provenance.py"),
    ("every component maps to a resource group", "extract_fom.py"),
    ("no colour carries two meanings", "fombees_palette.py"),
    ("summed ESM_BM agrees with each sheet's roll-up", "check_esmbm_rollup.py"),
    ("workbook formula hygiene", "check_formula_hygiene.py"),
    ("ESM conventions applied consistently", "check_conventions.py"),
    ("every dose and titer reads from Assumptions", "check_inputs_linked.py"),
    ("figures meet the journal specification", "check_nature_spec.py"),
    ("every printed number matches the model", "verify_plots.py"),
    ("every figure prints the values it must", "check_required_labels.py"),
]


def sh(script: str) -> tuple[int, str]:
    r = subprocess.run([PY, script], capture_output=True, text=True, cwd=HERE)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    fails = []
    print("regenerating figures")
    for f in FIGURES:
        code, out = sh(f)
        print(f"  {'ok  ' if code == 0 else 'FAIL'} {f}")
        if code:
            print(out[-1500:])
            fails.append(f)

    print("\nchecks")
    for name, script in CHECKS:
        code, out = sh(script)
        print(f"\n  == {name}")
        for line in out.splitlines():
            print(f"  {line}")
        if code:
            fails.append(name)

    print("\n" + "-" * 70)
    if fails:
        print(f"{len(fails)} FAILED: " + "; ".join(fails))
        return 1
    print("all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
