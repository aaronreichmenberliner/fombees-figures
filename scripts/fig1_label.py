"""Add panel labels to the supplied Figure 1 PDF, without re-rendering it.

The co-authors' artwork is six raster panels placed on one page. Those images
are left exactly as they are: the labels go on as a vector overlay and the page
is cropped to the content, so nothing is resampled and every panel keeps its
native resolution (316-592 dpi at the cropped size).

Panel positions were read from the page's own content stream rather than
measured by eye, so the labels cannot drift if the source is re-exported at a
different page size - the parse would simply fail instead.
"""
from __future__ import annotations

import io
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from pypdf import PdfReader, PdfWriter, Transformation

# imported for its rcParams: without it the overlay is written with the stock
# defaults and the label font is referenced rather than embedded, which fails
# the journal's font check
import fig_style  # noqa: F401
from fombees_paths import figure1_source, figures_dir

SRC = figure1_source()
STEM = "Figure1_block_flow"

# Reading order across the page, top row first. Matched to the scenarios by the
# panel positions in the co-authors' own composite slide.
ORDER = ["Im4", "Im5", "Im6", "Im1", "Im3", "Im2"]
SCENARIO = {"Im4": "FLOWN", "Im5": "TRANSGENIC-LETTUCE",
            "Im6": "TRANSGENIC-TOBACCO", "Im1": "GENE GUN",
            "Im3": "AGRO", "Im2": "VIRAL"}

LABEL_PT = 8.0          # matches the panel labels on Figures 2-6
GAP = 5.0               # between label and panel edge
PAD = dict(left=15.0, right=4.0, top=6.0, bottom=4.0)

PLACE = re.compile(
    r"q\s+([\d.]+)\s+0\s+0\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+cm\s*/(\w+)\s+Do")


def placements(page) -> dict[str, tuple[float, float, float, float]]:
    """(x, y, w, h) per image, straight from the page's content stream."""
    data = page.get_contents().get_data().decode("latin-1")
    out = {}
    for m in PLACE.finditer(data):
        w, h, x, y, name = m.groups()
        out[name] = (float(x), float(y), float(w), float(h))
    return out


def main() -> int:
    reader = PdfReader(str(SRC))
    page = reader.pages[0]
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)

    place = placements(page)
    missing = [k for k in ORDER if k not in place]
    if missing:
        print(f"  FAIL could not locate {missing} in the content stream; "
              f"found {sorted(place)}")
        return 1

    xs = [place[k][0] for k in ORDER] + [place[k][0] + place[k][2] for k in ORDER]
    ys = [place[k][1] for k in ORDER] + [place[k][1] + place[k][3] for k in ORDER]
    x0, x1 = min(xs) - PAD["left"], max(xs) + PAD["right"]
    y0, y1 = min(ys) - PAD["bottom"], max(ys) + PAD["top"]

    # the overlay is built at the source page size so it lines up exactly
    fig = plt.figure(figsize=(pw / 72, ph / 72))
    for i, key in enumerate(ORDER):
        x, y, w, h = place[key]
        fig.text((x - GAP) / pw, (y + h) / ph, "abcdef"[i],
                 fontsize=LABEL_PT, fontweight="bold", fontfamily="Helvetica",
                 ha="right", va="top", color="black")
    buf = io.BytesIO()
    # The bbox must be given as an explicit full-page Bbox. fig_style sets
    # savefig.bbox to "tight", and passing bbox_inches=None does NOT override
    # that - matplotlib falls back to the rcParam. Tight-cropping shrink-wraps
    # the overlay to the six glyphs, which then merge at the page origin and
    # land in a heap in the bottom-left corner instead of on the panels.
    fig.savefig(buf, format="pdf", transparent=True, pad_inches=0,
                bbox_inches=Bbox.from_bounds(0, 0, pw / 72, ph / 72))
    plt.close(fig)

    overlay = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
    # The overlay only lines up if it is the same size as the page it goes on.
    # Checked rather than assumed: a silently tight-cropped overlay still
    # merges without error, it just puts every label in the wrong place.
    ow, oh = float(overlay.mediabox.width), float(overlay.mediabox.height)
    if abs(ow - pw) > 0.5 or abs(oh - ph) > 0.5:
        print(f"  FAIL overlay is {ow:.1f} x {oh:.1f} pt, page is "
              f"{pw:.1f} x {ph:.1f}; labels would not align")
        return 1
    page.merge_page(overlay)

    # Shift the content so the cropped area starts at the origin, rather than
    # leaving a box with a non-zero lower-left corner. Several tools ignore the
    # offset and render from (0,0), which silently clips the left column; the
    # journal's own pipeline may be one of them.
    page.add_transformation(Transformation().translate(-x0, -y0))
    for box in (page.mediabox, page.cropbox, page.trimbox, page.artbox):
        box.lower_left = (0, 0)
        box.upper_right = (x1 - x0, y1 - y0)

    out = figures_dir() / f"{STEM}.pdf"
    w = PdfWriter()
    w.add_page(page)
    with open(out, "wb") as fh:
        w.write(fh)

    # 600 dpi companion for the Word file; the PDF is the version to submit
    import pymupdf
    pymupdf.open(out)[0].get_pixmap(dpi=600, alpha=False).save(
        figures_dir() / f"{STEM}.png")

    mm = 25.4 / 72
    print(f"  labelled {len(ORDER)} panels, no image resampled")
    for i, key in enumerate(ORDER):
        print(f"    {'abcdef'[i]}  {SCENARIO[key]}")
    print(f"\n  cropped to content: {(x1-x0)*mm:.0f} x {(y1-y0)*mm:.0f} mm "
          f"(was {pw*mm:.0f} x {ph*mm:.0f})")
    print(f"  wrote figures/{STEM}.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
