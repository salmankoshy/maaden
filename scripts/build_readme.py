"""Generate README.md from results/credit.json and results/results.json. Numbers are read, never typed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pct(d):
    if "zero_hit_bound" in d:
        return f"0 of {d['n']:,} (p < {d['zero_hit_bound']:.4f})"
    return f"{d['p']:.4f} [{d['lo']:.4f}, {d['hi']:.4f}]"


def credit_section(c):
    m, b = c["metrics"], c["base"]
    th = b["thresholds"]
    be = {(r["scenario"], r["threshold"]): r for r in c["breakeven"]}
    scen = {"flat": "FY25 EBITDA flat", "minus10": "x0.9", "minus20": "x0.8"}
    rows = "\n".join(
        f"| {label} | {be[(k, th['low'])]['breakeven_capex']:,.0f} | {be[(k, th['high'])]['breakeven_capex']:,.0f} | "
        f"{be[(k, th['high'])]['first_breach_year']} | {be[(k, th['high'])]['breakeven_capex_shock_floating']:,.0f} |"
        for k, label in scen.items())
    mat = "\n".join(f"| {r['year']} | {r['principal']:,.2f} | {100 * r['share']:.1f}% |" for r in c["maturities"])
    flat = be[("flat", th["high"])]
    wall = next(r for r in c["maturities"] if r["year"] == "2030")
    gap = 1 - b["capex_guidance_2026"] / flat["breakeven_capex"]
    gap_5 = 5 * round(100 * gap / 5)  # "about": nearest 5%
    return f"""## Credit core (deterministic, FY25 audited base)

How much capex can Ma'aden carry before leverage crosses its own ceiling? Base: audited balance sheet at 31-Dec-25, FY25 group EBITDA of SAR {b['ebitda']:,.0f}m. SAR m unless stated.

| Metric | Value |
|---|---|
| Net debt, leases excluded (company definition) | {m['net_debt']:,.2f} |
| Net debt / EBITDA | {m['leverage']:.3f}x |
| Net debt / EBITDA incl. leases | {m['leverage_incl_leases']:.3f}x |
| EBITDA fall to reach {th['low']}x / {th['high']}x | {100 * m['ebitda_cushion']['low']:.1f}% / {100 * m['ebitda_cushion']['high']:.1f}% |
| Interest cover, on borrowings interest / on total finance cost | {m['interest_cover_borrowings']:.2f}x / {m['interest_cover_finance_cost']:.2f}x |
| Liquidity (cash + time deposits + undrawn facilities) | {m['liquidity']:,.2f} |
| Floating share of principal | {100 * m['floating_share']:.1f}% |

**Breakeven capex.** Constant annual capex over 2026-2030 at which end-2030 net debt / EBITDA crosses the threshold (SAR m per year). 2026 guidance is {b['capex_guidance_2026']:,.0f}; holding it flat is an assumption.

| EBITDA scenario | Breakeven at {th['low']}x | Breakeven at {th['high']}x | First breach year at {th['high']}x | {th['high']}x with +{b['shock_bp']:.0f} bp on floating share |
|---|---|---|---|---|
{rows}

2026 capex guidance (SAR {b['capex_guidance_2026']:,.0f}m) sits about {gap_5:.0f}% below the {th['high']}x breakeven of SAR {flat['breakeven_capex']:,.0f}m.

**Rate sensitivity.** +{b['shock_bp']:.0f} bp on the floating share costs SAR {m['rate_shock_cost']:,.1f}m a year on today's principal and lowers the flat-EBITDA {th['high']}x breakeven from {flat['breakeven_capex']:,.0f} to {flat['breakeven_capex_shock_floating']:,.0f}. Applied to all debt it would be {flat['breakeven_capex_shock_all_debt']:,.0f}.

**Maturity wall.** {100 * wall['share']:.1f}% of principal falls due in 2030.

| Year | Principal | Share |
|---|---|---|
{mat}

![End-2030 leverage against capex](results/figures/credit_breakeven.png)

Excel version: [results/maaden_credit_model.xlsx](results/maaden_credit_model.xlsx). Formulas not machine-verified in a spreadsheet engine (`docs/decisions.md` section 22).

**Caveats**

- EBITDA is flat at FY25 (or a fixed multiple of it). Not a forecast.
- No EBITDA from new capacity, which is conservative: capex adds debt but earns nothing inside the horizon.
- Refinancing is assumed: maturities roll, so gross debt moves with free cash flow only.
- FY25 balance sheet; H1-26 is pending.
- Covenants are undisclosed. {th['high']}x is the top of management's target range, a management ceiling and not a covenant.
"""


def main():
    r = json.loads((ROOT / "results" / "results.json").read_text())
    c = json.loads((ROOT / "results" / "credit.json").read_text())
    f, s = r["modes"]["fixed"], r["modes"]["scaled"]
    bt = "\n".join(f"| {b['period']} | {b['predicted']:,.0f} | {b['actual']:,.0f} | {b['error_pct']:+.1f}% |"
                   for b in r["backtest"])
    th = r["thresholds"]
    text = f"""# Ma'aden capex financing stress test

Credit model for Ma'aden. Course project, INDENG 174. Plan: [maaden-build-plan.md](maaden-build-plan.md).

{credit_section(c)}
## Price-module prototype (v0.1)

A 12-month aluminium price module, built first as a prototype. It has no cash-flow waterfall and is not the credit result above.

### What v0.1 does

- Aluminium price: GBM, zero drift, fit on Pink Sheet monthly prices (sigma = {r['price']['sigma']:.4f}), {r['n_paths']:,} paths with antithetic pairs, 12 monthly steps from {r['anchor_date']}.
- Aluminium EBITDA: unit-cost model (b = {r['calibration']['basis_b']:.4f}, c = {r['calibration']['unit_cost_c_usd_t']:,.0f} USD/t produced), calibrated on H1-26.
- LTM EBITDA from 12 months of history (reported quarters, then model on actual prices) plus simulated months.
- Group EBITDA two ways: `fixed` (non-Al LTM held constant, lower bound on volatility) and `scaled` (Al LTM / Al share, upper bound).
- Net debt held at the 31-Dec-25 audited value, excluding leases ({r['anchors']['net_debt_sar_m']:,.2f} SAR m).
- Quarterly covenant-style test (months 3, 6, 9, 12) at {th['low']}x and {th['high']}x.

### What v0.1 does not do

- No other commodities, no correlation, no OU, no disruptions, no policies.
- No cash-flow waterfall: net debt does not move (no capex, interest, tax, dividends).
- Thresholds are analyst assumptions; covenant levels are not disclosed.
- Net debt anchor is 31-Dec-25 (H1-26 balance sheet not yet obtained).
- The unit-cost model does not back-test well outside H1-26 (below).

### Results (seed {r['seed']}, git {r['git_hash'][:7]})

Current leverage: fixed {r['current_leverage']['fixed']:.3f}x, scaled {r['current_leverage']['scaled']:.3f}x, reported-basis (LTM to Q2-26) {r['current_leverage']['reported_basis_ltm_q2_26']:.3f}x.

| | fixed | scaled |
|---|---|---|
| P(breach {th['low']}x), quarterly test (95% CI) | {pct(f['breach_quarterly_test']['low'])} | {pct(s['breach_quarterly_test']['low'])} |
| P(breach {th['high']}x), quarterly test | {pct(f['breach_quarterly_test']['high'])} | {pct(s['breach_quarterly_test']['high'])} |
| P(breach {th['low']}x), annual test | {pct(f['breach_annual_test']['low'])} | {pct(s['breach_annual_test']['low'])} |
| P95 leverage, month 12 | {f['leverage_month12_percentiles']['95.0']:.3f}x | {s['leverage_month12_percentiles']['95.0']:.3f}x |
| Median leverage, month 12 | {f['leverage_month12_percentiles']['50.0']:.3f}x | {s['leverage_month12_percentiles']['50.0']:.3f}x |

![month-12 leverage](results/figures/v01_hist.png)

Margin back-test (model at period-average Pink Sheet price, Q = production, SAR m):

| Period | Predicted | Actual | Error |
|---|---|---|---|
{bt}

## How to run

```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Python 3.11+
pytest
python scripts/run_all.py        # writes results/*.json, tables, figures and the Excel model
python scripts/build_readme.py   # regenerates this file from the result files
```

`run_all.py` never fetches data. Inputs are in `inputs/` (sourced, see `assumptions.csv`); modeling choices in `docs/decisions.md`.

## AI assistance
Built with Anthropic's Claude: Claude Code for code and tests, Claude chat for review and filing extraction. I chose the question, sourced and checked every input against Ma'aden's filings (page references in inputs/assumptions.csv), and made the modeling decisions (logged with reasons in docs/decisions.md).
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote README.md")


if __name__ == "__main__":
    main()
