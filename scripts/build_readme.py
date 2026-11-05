"""Generate README.md from results/results.json. Numbers are read, never typed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pct(d):
    if "zero_hit_bound" in d:
        return f"0 of {d['n']:,} (p < {d['zero_hit_bound']:.4f})"
    return f"{d['p']:.4f} [{d['lo']:.4f}, {d['hi']:.4f}]"


def main():
    r = json.loads((ROOT / "results" / "results.json").read_text())
    f, s = r["modes"]["fixed"], r["modes"]["scaled"]
    bt = "\n".join(f"| {b['period']} | {b['predicted']:,.0f} | {b['actual']:,.0f} | {b['error_pct']:+.1f}% |"
                   for b in r["backtest"])
    th = r["thresholds"]
    text = f"""# Ma'aden capex financing stress test (v0.1)

Monte Carlo leverage model for Ma'aden. Course project, INDENG 174. Plan: [maaden-build-plan.md](maaden-build-plan.md).

## What v0.1 does

- Aluminium price: GBM, zero drift, fit on Pink Sheet monthly prices (sigma = {r['price']['sigma']:.4f}), {r['n_paths']:,} paths with antithetic pairs, 12 monthly steps from {r['anchor_date']}.
- Aluminium EBITDA: unit-cost model (b = {r['calibration']['basis_b']:.4f}, c = {r['calibration']['unit_cost_c_usd_t']:,.0f} USD/t produced), calibrated on H1-26.
- LTM EBITDA from 12 months of history (reported quarters, then model on actual prices) plus simulated months.
- Group EBITDA two ways: `fixed` (non-Al LTM held constant, lower bound on volatility) and `scaled` (Al LTM / Al share, upper bound).
- Net debt held at the 31-Dec-25 audited value, excluding leases ({r['anchors']['net_debt_sar_m']:,.2f} SAR m).
- Quarterly covenant-style test (months 3, 6, 9, 12) at {th['low']}x and {th['high']}x.

## What v0.1 does not do

- No other commodities, no correlation, no OU, no disruptions, no policies.
- No cash-flow waterfall: net debt does not move (no capex, interest, tax, dividends).
- Thresholds are analyst assumptions; covenant levels are not disclosed.
- Net debt anchor is 31-Dec-25 (H1-26 balance sheet not yet obtained).
- The unit-cost model does not back-test well outside H1-26 (below).

## Results (seed {r['seed']}, git {r['git_hash'][:7]})

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
python scripts/run_all.py        # writes results/results.json and results/figures/v01_hist.png
python scripts/build_readme.py   # regenerates this file from results.json
```

`run_all.py` never fetches data. Inputs are in `inputs/` (sourced, see `assumptions.csv`); modeling choices in `docs/decisions.md`.
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote README.md")


if __name__ == "__main__":
    main()
