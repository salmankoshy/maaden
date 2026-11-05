# Ma'aden capex financing stress test (v0.1)

Monte Carlo leverage model for Ma'aden. Course project, INDENG 174. Plan: [maaden-build-plan.md](maaden-build-plan.md).

## What v0.1 does

- Aluminium price: GBM, zero drift, fit on Pink Sheet monthly prices (sigma = 0.1590), 10,000 paths with antithetic pairs, 12 monthly steps from 2026-10-01.
- Aluminium EBITDA: unit-cost model (b = 1.0632, c = 2,208 USD/t produced), calibrated on H1-26.
- LTM EBITDA from 12 months of history (reported quarters, then model on actual prices) plus simulated months.
- Group EBITDA two ways: `fixed` (non-Al LTM held constant, lower bound on volatility) and `scaled` (Al LTM / Al share, upper bound).
- Net debt held at the 31-Dec-25 audited value, excluding leases (21,626.45 SAR m).
- Quarterly covenant-style test (months 3, 6, 9, 12) at 2.5x and 3.0x.

## What v0.1 does not do

- No other commodities, no correlation, no OU, no disruptions, no policies.
- No cash-flow waterfall: net debt does not move (no capex, interest, tax, dividends).
- Thresholds are analyst assumptions; covenant levels are not disclosed.
- Net debt anchor is 31-Dec-25 (H1-26 balance sheet not yet obtained).
- The unit-cost model does not back-test well outside H1-26 (below).

## Results (seed 42, git 59f6676)

Current leverage: fixed 1.305x, scaled 1.277x, reported-basis (LTM to Q2-26) 1.317x.

| | fixed | scaled |
|---|---|---|
| P(breach 2.5x), quarterly test (95% CI) | 0 of 10,000 (p < 0.0003) | 0.1449 [0.1386, 0.1512] |
| P(breach 3.0x), quarterly test | 0 of 10,000 (p < 0.0003) | 0.0661 [0.0614, 0.0708] |
| P(breach 2.5x), annual test | 0 of 10,000 (p < 0.0003) | 0.1449 [0.1386, 0.1512] |
| P95 leverage, month 12 | 1.599x | 3.197x |
| Median leverage, month 12 | 1.415x | 1.713x |

![month-12 leverage](results/figures/v01_hist.png)

Margin back-test (model at period-average Pink Sheet price, Q = production, SAR m):

| Period | Predicted | Actual | Error |
|---|---|---|---|
| Q4-25 | 774 | 1,617 | -52.1% |
| Q3-25 | 532 | 755 | -29.6% |
| FY25 | 2,211 | 3,842 | -42.5% |
| FY24 | 1,346 | 2,950 | -54.4% |

## How to run

```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Python 3.11+
pytest
python scripts/run_all.py        # writes results/results.json and results/figures/v01_hist.png
python scripts/build_readme.py   # regenerates this file from results.json
```

`run_all.py` never fetches data. Inputs are in `inputs/` (sourced, see `assumptions.csv`); modeling choices in `docs/decisions.md`.
