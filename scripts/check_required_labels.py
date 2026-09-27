"""Assert that each figure actually PRINTS the values it exists to communicate.

verify_plots.py checks that every printed number is right. It cannot check that
a number is there at all - and that gap let Figure 5 ship with all six of its
ESM_BM labels silently clipped away by an annotate() placed outside the axes.
This is the complement: a required-value manifest per figure.
"""
from __future__ import annotations

import re
import sys

from pypdf import PdfReader

from fombees_paths import figures_dir
from load import totals
from read_esmbm import read

r, tot = read(), totals()
ORDER = sorted(r, key=lambda s: r[s]["ESM_BM"])


def money(v: float) -> str:
    return f"{v:,.0f}"


REQUIRED = {
    # Figure 3 no longer carries an ESMBM panel; its net values are the four
    # figures of merit, and the ESMBM totals are required of Figure 4 instead.
    "Figure3_cross_scenario":
        [f"{tot[(s, 'power', 'Net')]:.3f}" for s in ORDER
         if 0 < tot[(s, 'power', 'Net')] < 1],
    "Figure4_ESM_BM": [money(r[s]["ESM_BM"]) for s in ORDER],
}


def expected_sequences() -> dict[str, list[tuple[str, list[str]]]]:
    """Exact ordered token runs each figure must contain.

    Panels that print ranks and rounded percentages cannot be verified by pool
    membership - almost any wrong small integer is some other legitimate value,
    and a substitution test measured 73-85% of wrong values passing. Verifying
    the ordered sequence instead pins each cell to its own expected value.
    """
    from extract_fom import CREDIT
    from load import METRICS

    cols = METRICS + ["esm"]

    recovery, ranks = [], []
    for sc in ORDER:
        for m in METRICS:
            g = tot[(sc, m, "Gross")]
            recovery.append(f"{100 * tot.get((sc, m, CREDIT), 0.0) / g:.0f}"
                            if g else "0")
        recovery.append(f"{100 * r[sc]['Useful process outputs'] / r[sc]['GROSS']:.0f}")

    rank_of = {m: {s2: i + 1 for i, s2 in
                   enumerate(sorted(ORDER, key=lambda x: tot[(x, m, "Net")]))}
               for m in METRICS}
    for sc in ORDER:
        for m in METRICS:
            ranks.append(str(rank_of[m][sc]))
        ranks.append(str(ORDER.index(sc) + 1))

    return {
        "Figure5_ESM_BM_vs_FOM": [("panel a recovery matrix", recovery),
                                  ("panel b rank matrix", ranks)],
    }


def ordered_tokens(pdf) -> list[str]:
    parts: list[str] = []
    for page in PdfReader(pdf).pages:
        page.extract_text(visitor_text=lambda t, *_a: parts.append(t))
    out = []
    for part in parts:
        for tok in re.split(r"[\s%()/]+", part):
            tok = tok.strip().rstrip(".,")
            if tok:
                out.append(tok)
    return out


def contains(haystack: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def printed(pdf) -> set[str]:
    parts: list[str] = []
    for page in PdfReader(pdf).pages:
        page.extract_text(visitor_text=lambda t, *_a: parts.append(t))
    out = set()
    for part in parts:
        for tok in re.split(r"[\s%()]+", part):
            tok = tok.strip().rstrip(".,")
            if tok:
                out.add(tok)
    return out


def run() -> list[str]:
    bad = []
    for stem, want in REQUIRED.items():
        pdf = figures_dir() / f"{stem}.pdf"
        if not pdf.exists():
            bad.append(f"{stem}: not rendered")
            continue
        have = printed(pdf)
        missing = [w for w in want if w not in have]
        status = "ok " if not missing else "BAD"
        print(f"  {status} {stem:<34} {len(want) - len(missing)}/{len(want)} "
              f"required values present")
        if missing:
            print(f"        missing: {', '.join(missing)}")
            bad.append(f"{stem}: missing {len(missing)}")

    for stem, seqs in expected_sequences().items():
        pdf = figures_dir() / f"{stem}.pdf"
        if not pdf.exists():
            continue
        toks = ordered_tokens(pdf)
        for label, want in seqs:
            ok = contains(toks, want)
            print(f"  {'ok ' if ok else 'BAD'} {stem:<34} {label} "
                  f"({len(want)} values, exact order)")
            if not ok:
                print(f"        expected: {' '.join(want)}")
                bad.append(f"{stem}: {label} does not match")
    return bad


if __name__ == "__main__":
    fails = run()
    print("  every figure prints the values it must" if not fails
          else f"  {len(fails)} figure(s) missing required values")
    sys.exit(1 if fails else 0)
