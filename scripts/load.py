"""Aggregate the extracted component rows into the shapes the figures need."""
from __future__ import annotations

from collections import defaultdict

from extract_fom import CREDIT, SCEN, rows

METRICS = ["mass", "volume", "power", "crew_time"]
# Flows that are a cost. CREDIT ("Output") is subtracted.
COST_FLOWS = ["System", "Process Operations", "Input", "Waste"]

_cache: list[dict] | None = None


def _rows() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = rows()
    return _cache


def totals() -> dict[tuple[str, str, str], float]:
    """(scenario, metric, flow) -> value, plus the derived 'Gross' and 'Net'."""
    t: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in _rows():
        t[(r["scenario"], r["metric"], r["flow"])] += r["value"]
    for s in SCEN:
        for m in METRICS:
            gross = sum(t.get((s, m, f), 0.0) for f in COST_FLOWS)
            t[(s, m, "Gross")] = gross
            t[(s, m, "Net")] = gross - t.get((s, m, CREDIT), 0.0)
    return dict(t)


def by_group() -> dict[tuple[str, str, str, str], float]:
    """(scenario, metric, flow, resource group) -> value."""
    g: dict[tuple[str, str, str, str], float] = defaultdict(float)
    for r in _rows():
        g[(r["scenario"], r["metric"], r["flow"], r["group"])] += r["value"]
    return dict(g)


if __name__ == "__main__":
    t = totals()
    for m in METRICS:
        print(f"=== {m}")
        print(f"{'':<20}" + "".join(f"{f:>12}" for f in COST_FLOWS)
              + f"{'Credit':>12}{'Net':>13}")
        for s in sorted(SCEN, key=lambda x: t[(x, m, "Net")]):
            vals = [t.get((s, m, f), 0.0) for f in COST_FLOWS]
            print(f"{s:<20}" + "".join(f"{v:>12,.3f}" for v in vals)
                  + f"{t.get((s, m, CREDIT), 0.0):>12,.3f}"
                  + f"{t[(s, m, 'Net')]:>13,.3f}")
        print()
