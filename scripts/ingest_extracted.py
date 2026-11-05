"""Map source/maaden_extracted_inputs.csv into inputs/assumptions.csv and inputs/segments.csv.

Values are copied as strings, exactly as extracted. Nothing is converted or rounded.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source" / "maaden_extracted_inputs.csv"
ASSUMP = ROOT / "inputs" / "assumptions.csv"
SEGMENTS = ROOT / "inputs" / "segments.csv"

ASSUMP_COLS = ["key", "value", "unit", "period", "source", "page", "date_retrieved", "source_url", "note"]
SEG_COLS = ["period", "segment", "sales", "ebitda", "volume", "volume_unit", "realized_price", "source", "page"]

# Placeholder keys with no counterpart in the extract; kept as NOT_FILLED.
STILL_NOT_FILLED = [
    ("corporate_ebitda", "Segment note; not in extract (derive from group minus segments in checks only)"),
]


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8", newline="")))
    with open(ASSUMP, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=ASSUMP_COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in ASSUMP_COLS})
        for k, src in STILL_NOT_FILLED:
            w.writerow({"key": k, "value": "NOT_FILLED", "source": src})

    seg_keys = {
        "al_sales": ("aluminum", "sales"),
        "al_ebitda": ("aluminum", "ebitda"),
        "al_production_kmt": ("aluminum", "production"),
        "al_sales_volume_kmt": ("aluminum", "sales_volume"),
        "al_realized_usd_t": ("aluminum", "realized_price"),
        "phosphate_ebitda": ("phosphate", "ebitda"),
        "bmnm_ebitda": ("bmnm", "ebitda"),
    }
    table = {}
    for r in rows:
        if r["key"] not in seg_keys:
            continue
        seg, field = seg_keys[r["key"]]
        cell = table.setdefault((r["period"], seg), {"source": set(), "page": set()})
        cell[field] = r["value"]
        if r["source"]:
            cell["source"].add(r["source"])
        if r["page"]:
            cell["page"].add(r["page"])
    order = lambda k: (k[1], k[0])
    with open(SEGMENTS, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(SEG_COLS)
        for (period, seg) in sorted(table, key=order):
            c = table[(period, seg)]
            # Volume = production throughout (2026 sales volumes are not disclosed; see decisions.md).
            vol, unit = (c["production"], "kmt production") if "production" in c else ("", "")
            w.writerow([period, seg, c.get("sales", ""), c.get("ebitda", ""), vol, unit,
                        c.get("realized_price", ""), " | ".join(sorted(c["source"])),
                        " | ".join(sorted(c["page"]))])
    print(f"assumptions: {len(rows)} extracted rows + {len(STILL_NOT_FILLED)} placeholder")


if __name__ == "__main__":
    main()
