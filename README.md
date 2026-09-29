# FOMBEES — figures

Everything needed to regenerate the figures in *Figures of Merit and Equivalent
System Mass for Space-Based Production of a Therapeutic in Plants*, from the
Supplementary Information workbook that the paper reports.

Every number printed in every figure is read from `data/`, not typed into a
script. The checks in `scripts/` verify that, and fail loudly when it stops
being true.

## Quick start

```bash
make setup          # creates .venv and installs pinned dependencies
source .venv/bin/activate
make figures        # renders Figures 1-6 into figures/
make check          # regenerates, then runs all ten checks
```

Or without `make`:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd scripts && python fig1_label.py && python fig2.py ...   # or: python verify_all.py
```

Python 3.11 or newer. Figure 6 needs the `formulas` package because it
recomputes the workbook; the other figures do not. Figure 1 needs `pypdf` and
`pymupdf`, since it labels a supplied PDF rather than plotting anything.

## What is here

```
data/      the Supplementary Information workbook, unmodified, and the
           co-authors' Figure 1 artwork before labelling
scripts/   the pipeline and its checks
figures/   rendered output: vector PDF plus 600 dpi PNG
```

The rendered figures are committed so the repository can be read without
running anything. `make figures` reproduces them exactly: the output is
pixel-identical from a clean checkout, verified.

## How it works

The workbook is the single source of truth. Nothing downstream caches a value
from it without recording which workbook it came from.

**`extract_fom.py`** reads the per-component figure-of-merit tables. Each
scenario sheet carries a `FOM Graphs` block, located by its own label rather
than a fixed row, because the blocks sit at different rows on every sheet. The
column layout (mass, volume, power, crew time; system, input, output, waste) is
asserted against the block's own header row, so a rearranged sheet fails rather
than being silently misread. Every component is mapped to one of eight resource
groups, and an unmapped component is an error.

**`read_esmbm.py`** computes ESM_BM per scenario as
`System + Process Operations + Process Inputs + Waste − Useful`, summing the
five category rows. Label handling matters more than it looks: the sheets do
not spell those categories identically, and matching only the canonical
spelling once dropped 124 kg_eq of FLOWN waste through five published figures.

**`load.py`** aggregates components into the shapes the figures need.

**`fig1_label.py`** is the exception to everything above. Figure 1 is block-flow
artwork drawn by the co-authors, not a plot of the model, so it is not redrawn.
The script adds the a–f panel labels as a vector overlay and crops the page;
the six embedded images are left byte-identical to the source, so nothing is
resampled. Panel positions are read from the PDF's own content stream, and
the overlay is checked to be the same size as the page before merging, since
a mis-sized overlay merges without error and puts every label in the wrong place.

**`sensitivity.py`** derives Figure 6 by recomputing the workbook with one
input perturbed, not by an analytic approximation. Plant and equipment counts
pass through integer rounding, so the real response is step-wise and no smooth
formula reproduces it. Results are cached and stamped with a hash of the
workbook they came from; a cache built from a different workbook is rejected.

**`fombees_palette.py`** holds every colour and line style, with the invariants
the figures rely on: no colour carries two meanings within one encoding, no
figure mixes two encodings, resource groups stay separable in greyscale, and
no figure invents a dash pattern. Solid means a scenario, dashed the FLOWN
reference, dotted a parameter value in use.

**`fig_style.py`** carries the journal specification. Two details drive the
odd-looking parts: exponents use Unicode superscripts rather than mathtext,
because matplotlib renders mathtext at exactly 0.700 of the base size and a
6 pt label would put the exponent below the 5 pt floor; and the labels that
genuinely need a subscript (ESM_BM, kg_eq) are set at 7.2 pt so the subscript
lands at 5.04 pt, just inside spec.

## The checks

`python verify_all.py` regenerates every figure and then runs ten checks. The
ordering is deliberate: the figures are rendered first, or the checks that read
the PDFs would test stale output.

| check | what it establishes |
|---|---|
| `check_sheet_provenance` | every figure traces to the current workbook, by content hash rather than timestamp |
| `extract_fom` | every component maps to a resource group |
| `fombees_palette` | no colour or dash pattern carries two meanings |
| `check_esmbm_rollup` | the summed totals agree with each sheet's own total, and the parts sum to the whole |
| `check_formula_hygiene` | no duplicated term in a sum, no arithmetic on a blank cell |
| `check_conventions` | the two ESM conventions are applied identically on every sheet |
| `check_inputs_linked` | every dose and titer reads from the Assumptions tab rather than being typed in |
| `check_nature_spec` | width, embedded fonts, and all text between 5 and 8 pt, read from the PDF |
| `verify_plots` | every number printed in a figure matches a model value |
| `check_required_labels` | every figure prints the values it must, in the right order |

Two of these exist because of specific failures, and are worth explaining.

`check_sheet_provenance` compares content hashes, not modification times. A
derived cache once got copied into a new working directory, which made it
*newer* than the workbook while its contents still came from the previous one.
A timestamp test passes in that situation.

`check_required_labels` verifies that expected numbers are **present**, not
just that printed numbers are right. Figure 5 once shipped with all six of its
labels clipped away by an annotation placed one unit outside the axes, under a
green build, because nothing checked for absence. Where a panel prints ranks or
rounded percentages it is checked positionally, cell by cell, since pool
membership cannot distinguish a wrong small integer from a right one.

Every check has been tested by injecting the fault it is meant to catch.

## Conventions worth knowing before reading the numbers

Two that explain why the figure-of-merit tables and the ESM tables do not
reconcile arithmetically. Both are deliberate and both are stated in the paper:

- Water is priced through its treatment factor alone and excluded from the mass
  and volume terms, so it is not counted twice.
- Waste carries mass only; waste volume is not charged. This is a real
  limitation rather than bookkeeping — GENE GUN's 7.78 m³ of waste volume is
  about 617 kg_eq the metric never prices.

`check_conventions.py` asserts both, and prints the unpriced waste volume per
scenario.

## Licence

Two licences, because the repository holds two different kinds of thing.

| | licence | file |
|---|---|---|
| `scripts/` | MIT | `LICENSE` |
| `data/`, `figures/` | CC BY 4.0 | `LICENSE-DATA` |

Reuse the code freely. Reuse the workbook or the figures freely too, including
commercially, but credit the paper and say if you changed them. The citation to
use is in `LICENSE-DATA`.

## Figures

| | |
|---|---|
| **1** | block flow of the six production scenarios (co-authors' artwork, labelled here) |
| **2** | figures of merit by resource group, 24 panels |
| **3** | net figures of merit across all six scenarios |
| **4** | batch-manufacturing equivalent system mass, ESM_BM |
| **5** | useful-output recovery, and rank under each single resource |
| **6** | sensitivity to the crew-time factor, expression level, weekly dose and number of batches |

Captions are in the manuscript, not here.
