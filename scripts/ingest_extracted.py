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

ANALYST = "Analyst assumption; see docs/decisions.md"
# Model configuration (no literals in src/). key, value, unit, note
MODEL_PARAMS = [
    ("sim_n_paths", "10000", "paths", "Even number; antithetic pairs"),
    ("sim_seed", "42", "", "Rule 4"),
    ("sim_n_months", "12", "months", "v0.1 horizon"),
    ("months_per_year", "12", "months", "Unit constant (dt = 1/months_per_year)"),
    ("price_fit_start", "2010-01-01", "date", "GBM fit window start; end = price_anchor_date"),
    ("drift_mode", "zero", "", "zero | historical"),
    ("ci_level", "0.95", "", "Normal-approx CI on pair means"),
    ("percentiles", "5,25,50,75,95", "", "Percentiles of month-12 leverage"),
    ("zero_hit_bound_k", "3", "", "Rule of three: p < k/n when no breaches"),
    ("calib_quarters", "Q1-26,Q2-26", "", "Basis b and unit cost c anchored on H1-26"),
    ("ltm_hist_quarters", "Q3-25,Q4-25,Q1-26,Q2-26", "", "Reported quarters feeding the LTM and non-Al LTM"),
    ("backtest_periods", "Q4-25,Q3-25,FY25,FY24", "", "Periods with production volumes for the margin back-test"),
    ("nd_anchor_period", "31-Dec-25", "", "Balance sheet date for net debt"),
]


def derived_corporate(rows):
    """corporate_ebitda = sum(segment EBITDA) - group EBITDA (positive = corporate cost/eliminations)."""
    from decimal import Decimal
    fx = Decimal(next(r["value"] for r in rows if r["key"] == "fx_sar_per_usd"))
    val = {(r["key"], r["period"]): r for r in rows}
    out = []
    for p in ["Q2-26", "Q1-26", "Q4-25", "Q3-25", "Q2-25", "FY25"]:
        try:
            segs = sum(Decimal(val[(k, p)]["value"]) for k in ("al_ebitda", "phosphate_ebitda", "bmnm_ebitda"))
            g = val[("group_ebitda", p)]
        except KeyError:
            continue
        gv = Decimal(g["value"]) * (fx if g["unit"] == "USD m" else 1)
        note = "sum(al,phosphate,bmnm EBITDA) - group EBITDA; positive = corporate cost/eliminations"
        if g["unit"] == "USD m":
            note += f"; group converted from USD m at {fx}"
        out.append({"key": "corporate_ebitda", "value": str(segs - gv), "unit": "SAR m", "period": p,
                    "source": "DERIVED", "date_retrieved": g["date_retrieved"], "note": note})
    return out


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8", newline="")))
    with open(ASSUMP, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=ASSUMP_COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in ASSUMP_COLS})
        for rec in derived_corporate(rows):
            w.writerow(rec)
        for k, v, unit, note in MODEL_PARAMS:
            w.writerow({"key": k, "value": v, "unit": unit, "source": ANALYST,
                        "date_retrieved": rows[0]["date_retrieved"], "note": note})

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
    print(f"assumptions: {len(rows)} extracted rows + derived corporate + {len(MODEL_PARAMS)} model params")


if __name__ == "__main__":
    main()
