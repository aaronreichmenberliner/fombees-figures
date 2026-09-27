"""Check the rendered PDFs against the journal figure specification.

Read from the PDF rather than from the plotting code, because the spec applies
to what is actually rendered. Two failure modes this has caught before:
mathtext exponents, which matplotlib renders at 0.7x the nominal size and which
therefore fall below the 5 pt floor from a nominally compliant 7 pt label; and
text converted to outlines, which is invisible to a font check but fails
production.
"""
from __future__ import annotations

import re
import sys

from pypdf import PdfReader

from fombees_paths import figures_dir

FLOOR, CEILING = 5.0, 8.0
MAX_WIDTH_MM = 183.0 + 0.5
MAX_HEIGHT_MM = 247.0
PT_PER_MM = 72.0 / 25.4
TF = re.compile(rb"/(\w+)\s+([\d.]+)\s+Tf")


def sizes(page) -> list[float]:
    """Font sizes set by Tf operators in the content stream.

    These are nominal sizes. matplotlib writes text at its true point size and
    does not scale via the text matrix, so Tf is the rendered size here - but
    this does NOT account for a scaling Tm, and would under-report if the
    figure were produced by a tool that used one.
    """
    data = page.get_contents().get_data()
    return [float(m.group(2)) for m in TF.finditer(data)]


def run() -> list[str]:
    bad = []
    for pdf in sorted(figures_dir().glob("Figure*.pdf")):
        reader = PdfReader(pdf)
        page = reader.pages[0]
        w = float(page.mediabox.width) / PT_PER_MM
        h = float(page.mediabox.height) / PT_PER_MM
        problems = []
        if w > MAX_WIDTH_MM:
            problems.append(f"width {w:.1f} mm exceeds 183 mm")
        if h > MAX_HEIGHT_MM:
            problems.append(f"height {h:.1f} mm exceeds 247 mm")

        fonts, embedded = set(), 0
        res = page.get("/Resources", {}).get("/Font", {})
        for key in res:
            f = res[key].get_object()
            fonts.add(str(f.get("/BaseFont", "?")))
            desc = f.get("/FontDescriptor")
            if desc is None and f.get("/Subtype") == "/Type0":
                df = f.get("/DescendantFonts")
                if df:
                    desc = df[0].get_object().get("/FontDescriptor")
            if desc is not None:
                d = desc.get_object()
                if any(k in d for k in ("/FontFile2", "/FontFile3", "/FontFile")):
                    embedded += 1
        if not fonts:
            problems.append("no fonts at all - text may be outlined, which "
                            "fails production")
        elif embedded < len(fonts):
            problems.append(f"{len(fonts) - embedded} of {len(fonts)} fonts "
                            "not embedded")

        ss = [s for p in reader.pages for s in sizes(p)]
        small = sorted({s for s in ss if 0 < s < FLOOR})
        large = sorted({s for s in ss if s > CEILING})
        if small:
            problems.append(f"text below {FLOOR} pt: "
                            + ", ".join(f"{s:g}" for s in small))
        if large:
            problems.append(f"text above {CEILING} pt: "
                            + ", ".join(f"{s:g}" for s in large))

        status = "ok " if not problems else "BAD"
        rng = f"{min(ss):g}-{max(ss):g} pt" if ss else "no text"
        emb = ("all embedded" if embedded == len(fonts)
               else f"{embedded}/{len(fonts)} embedded")
        print(f"  {status} {pdf.name:<42} {w:5.1f} x {h:5.1f} mm, "
              f"{len(fonts)} font(s) {emb}, text {rng}")
        for p in problems:
            print(f"        {p}")
            bad.append(f"{pdf.name}: {p}")
    return bad


if __name__ == "__main__":
    fails = run()
    print("  all figures meet the specification" if not fails
          else f"  {len(fails)} specification failure(s)")
    sys.exit(1 if fails else 0)
