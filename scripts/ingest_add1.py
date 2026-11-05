"""Append source/maaden_extracted_inputs_add1.csv and the credit-core ANALYST settings to inputs/assumptions.csv.

Existing rows are never touched. Values are copied as strings. Stops (non-zero exit) if a check fails or if the
rows are already there. Run scripts/ingest_extracted.py first if assumptions.csv is ever rebuilt from scratch.
"""
import csv
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source" / "maaden_extracted_inputs_add1.csv"
ASSUMP = ROOT / "inputs" / "assumptions.csv"
RETRIEVED = "2026-11-04"
N_ADD1 = 97

# key, value, unit, period, note. Scenario settings: analyst choices, not filing data.
ANALYST_PARAMS = [
    ("credit_ebitda_multiplier", "1.0", "x", "flat", "Scenario: FY25 group EBITDA held flat"),
    ("credit_ebitda_multiplier", "0.9", "x", "minus10", "Scenario: FY25 group EBITDA x0.9, held flat"),
    ("credit_ebitda_multiplier", "0.8", "x", "minus20", "Scenario: FY25 group EBITDA x0.8, held flat"),
    ("credit_threshold", "2.5", "x", "low", "Inside company 2-3x target range; not a covenant"),
    ("credit_threshold", "3.0", "x", "high", "Top of company 2-3x target range; management ceiling, not a covenant"),
    ("credit_rate_shock_bp", "100", "bp", "", "Rate sensitivity"),
    ("credit_first_year", "2026", "year", "", "First waterfall year (from 31-Dec-25)"),
    ("credit_last_year", "2030", "year", "", "Last waterfall year"),
    ("credit_capex_search_low", "0", "SAR m", "", "Bisection lower bound"),
    ("credit_capex_search_high", "60000", "SAR m", "", "Bisection upper bound"),
    ("credit_capex_search_tol", "0.01", "SAR m", "", "Bisection stopping width"),
    ("credit_chart_capex_low", "8000", "SAR m", "", "Breakeven chart x-axis start"),
    ("credit_chart_capex_high", "25000", "SAR m", "", "Breakeven chart x-axis end"),
    ("credit_chart_capex_step", "250", "SAR m", "", "Breakeven chart x-axis step"),
    ("credit_mc_capex_low", "10000", "SAR m", "", "Tier 2 capex grid start"),
    ("credit_mc_capex_high", "22000", "SAR m", "", "Tier 2 capex grid end"),
    ("credit_mc_capex_step", "500", "SAR m", "", "Tier 2 capex grid step"),
    ("credit_mc_curve_x_low", "2", "x", "", "Tier 2 breach curve start"),
    ("credit_mc_curve_x_high", "5", "x", "", "Tier 2 breach curve end"),
    ("credit_mc_curve_x_step", "0.05", "x", "", "Tier 2 breach curve step"),
    ("credit_mc_ci_z", "1.96", "", "", "Normal quantile for 95% CI on antithetic pair means"),
]


def rows_for(key, rows):
    return [r for r in rows if r["key"] == key]


def checks(rows):
    """Stop-the-run checks on add1, in exact decimal arithmetic."""
    mat = sum(Decimal(r["value"]) for r in rows_for("debt_maturity_principal", rows))
    one = lambda k: rows_for(k, rows)[0]["value"]
    out = [
        ("rows", len(rows), N_ADD1),
        ("maturity sum", mat, Decimal("32528.83")),
        ("tau_eff", Decimal(one("tau_eff")), Decimal("0.1498")),
        ("effective_interest_rate", Decimal(one("effective_interest_rate")), Decimal("0.0538")),
        ("fixed_rate_share", Decimal(one("fixed_rate_share")), Decimal("0.1741")),
    ]
    failed = [c for c in out if c[1] != c[2]]
    for name, got, want in out:
        print(f"  {'ok ' if got == want else 'FAIL'} {name}: {got} (expected {want})")
    return not failed


def main():
    add1 = list(csv.DictReader(open(SRC, encoding="utf-8", newline="")))
    if not checks(add1):
        sys.exit("add1 checks failed; nothing written")
    with open(ASSUMP, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols, existing = reader.fieldnames, list(reader)
    have = {(r["key"], r["period"]) for r in existing}
    new_keys = {(r["key"], r["period"]) for r in add1} | {(p[0], p[3]) for p in ANALYST_PARAMS}
    if have & new_keys:
        sys.exit(f"already ingested, nothing written: {sorted(have & new_keys)[:3]}")
    with open(ASSUMP, "a", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writerows({c: r[c] for c in cols} for r in add1)
        for key, value, unit, period, note in ANALYST_PARAMS:
            w.writerow({"key": key, "value": value, "unit": unit, "period": period, "source": "ANALYST",
                        "page": "", "date_retrieved": RETRIEVED, "source_url": "", "note": note})
    print(f"appended {len(add1)} add1 rows + {len(ANALYST_PARAMS)} ANALYST rows")


if __name__ == "__main__":
    main()
