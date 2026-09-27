"""Locate the repo's inputs and outputs.

The repo root is the directory holding the draft 8 workbook and manuscript.
Resolved by walking up from this file so the scripts work whether they are run
from the analysis directory, the repo root, or a flat redistribution bundle.
"""
from pathlib import Path

WORKBOOK_NAME = "FOMBEES Supplemental Information FINAL.xlsx"
MANUSCRIPT_NAME = "FOMBEES Manuscript Draft 9.docx"


def _root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here.parent, *here.parents):
        if (cand / WORKBOOK_NAME).exists():
            return cand
        if (cand / "data" / WORKBOOK_NAME).exists():   # bundle layout
            return cand
    raise FileNotFoundError(
        f"could not find {WORKBOOK_NAME} in any parent of {here}")


ROOT = _root()


def _find(name: str) -> Path:
    for cand in (ROOT / name, ROOT / "data" / name):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"{name} not under {ROOT}")


def workbook() -> Path:
    return _find(WORKBOOK_NAME)


def manuscript() -> Path:
    return _find(MANUSCRIPT_NAME)


def figures_dir() -> Path:
    d = ROOT / "figures"
    d.mkdir(exist_ok=True)
    return d


if __name__ == "__main__":
    print("root:      ", ROOT)
    print("workbook:  ", workbook())
    print("manuscript:", manuscript())
    print("figures:   ", figures_dir())
