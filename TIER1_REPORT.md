# Tier 1 report: credit core

Branch `credit-core`. Not tagged, not pushed. All SAR m unless stated.

## Steps

| Step | Status | Commit |
|---|---|---|
| 1. Ingest add1 (97 rows); all stop-the-run checks passed | done | f3d3344 |
| 2. `src/credit.py` metrics | done | b797764 |
| 3. Waterfall and breakeven | done | e6d7446 |
| 4. Tests | done | 3e54d91 |
| 5. `results/credit.json`, `results/tables/*.csv` | done | 018c109 |
| 6. Excel model | done, formulas not machine-verified | 95a0214 |
| 7. Chart `results/figures/credit_breakeven.png` | done | eadc4c8 |
| 8. README | done | 412b52d |
| 9. This report | done | see `git log` |

## Tests

37 passed, 0 failed (`.venv/Scripts/python.exe -m pytest`, Python 3.13.2, pinned requirements). Every target in step 4 is asserted in `tests/test_credit.py`.

## The +100 bp check

| Shock applied to | Effective rate | Flat-EBITDA 3.0x breakeven | Fall from 17,113 |
|---|---|---|---|
| Floating share only (the published case) | 5.38% + 0.826 x 1% = 6.206% | 16,817 | 296 |
| All debt (your reference value, 16,755 ±5) | 6.38% | 16,755 | 358 |

The floating case is 62 higher because only 82.6% of debt reprices, so the rate rises 82.6 bp and not 100. The fall in breakeven scales about the same way: 358 x 0.826 = 296. The share is held at its 31-Dec-25 value on all debt, including new debt.

## Published numbers

Source rows are `key (period)` in `inputs/assumptions.csv`.

| Number | Value | Formula | Source rows |
|---|---|---|---|
| Net debt | 21,626.45 | borrowings - cash - TD | total_borrowings, cash_and_equivalents, time_deposits (31-Dec-25) |
| Net debt incl. leases | 23,041.30 | ND + leases | + lease_liabilities (31-Dec-25) |
| Leverage | 1.338x | ND / EBITDA | + group_ebitda (FY25) |
| Leverage incl. leases | 1.426x | as above | as above |
| EBITDA cushion to 2.5x / 3.0x | 46.5% / 55.4% | 1 - ND/(x * EBITDA) | + credit_threshold (low, high) |
| Interest cover, borrowings | 8.756x | EBITDA / interest | interest_expense_borrowings (FY25) |
| Interest cover, finance cost | 7.438x | EBITDA / finance cost | finance_cost (FY25) |
| Liquidity | 25,252.97 | cash + TD + undrawn | undrawn_facilities (31-Dec-25) |
| Floating share | 82.59% | 1 - sukuk / principal | sukuk_fixed_principal, debt_principal_total (31-Dec-25) |
| +100 bp annual cost | 268.65 | share * principal * shock | + credit_rate_shock_bp |
| 2030 maturity share | 23.43% | 7,622.71 / principal | debt_maturity_principal (2030) |
| Breakeven 2.5x / 3.0x, flat | 15,639 / 17,113 | bisection on capex for L_2030 > x | waterfall rows below |
| Breakeven 2.5x / 3.0x, x0.9 | 13,528 / 14,855 | same | + credit_ebitda_multiplier (minus10) |
| Breakeven 2.5x / 3.0x, x0.8 | 11,416 / 12,596 | same | + credit_ebitda_multiplier (minus20) |
| Breakeven 2.5x / 3.0x, x1.0, +100 bp floating | 15,363 / 16,817 | same, r + share * shock | + credit_rate_shock_bp |
| Breakeven 2.5x / 3.0x, x0.9, +100 bp floating | 13,262 / 14,571 | same | same |
| Breakeven 2.5x / 3.0x, x0.8, +100 bp floating | 11,161 / 12,325 | same | same |
| L_2030 at guidance capex, flat | 2.45x | waterfall | capex_guidance_2026 (FY26) |
| First breach year at every breakeven | 2030 | first t with L_t > x | waterfall |

Waterfall rows: total_borrowings, cash_and_equivalents, time_deposits (31-Dec-25); group_ebitda, effective_interest_rate, tau_eff, da_total, dividends_to_nci_fy25 (FY25).

## Unverified or worth your check

- **Excel: formulas not machine-verified.** LibreOffice is not installed. A Python evaluator in `tests/test_credit_xlsx.py` matches Metrics, Waterfall and Maturities to `src/credit.py` within 0.01 at three capex levels, but no spreadsheet engine has run the file. It also has no cached values, so previewers show blanks until Excel opens it. Open it once in Excel and check `Metrics!B5` shows 1.338x.
- **Inputs were not re-checked against the PDFs.** The checks confirm the extract's internal arithmetic (for example maturities sum to principal). They don't confirm that the extract matches the filing.
- **Negative debt at low capex.** With zero capex, D goes negative from 2028 and earns interest at 5.38%. Far from any breakeven, so it doesn't affect a published number. Logged in `docs/decisions.md` section 21.
- **`tau_eff` includes severance fees.** The source note gives 2.43% excluding them. The tax base applies 14.98% to EBITDA - D&A - interest, per your spec.
- **First breach year is always 2030.** This follows from how breakeven is defined and from leverage rising steadily at those capex levels. It carries little independent information.

## Environment and repo notes

- **Use `.venv`.** System `python` is 3.8, which fails `test_h` with a `write_text(newline=)` error on the unmodified v0.1 code. `.venv` is Python 3.13 with pinned packages and passes.
- **`results/results.json` was already modified when I started and I left it uncommitted.** It differs from HEAD only in `git_hash`. Every `pytest` run rewrites it.
- **`run_all.py` now also runs the credit outputs**, so `pytest` rewrites `results/credit.json` and the `.xlsx` too. The `.xlsx` differs in bytes each run because of its save timestamp, and the `git_hash` stored in a committed result is the parent commit.
- **`scripts/ingest_extracted.py` rebuilds `assumptions.csv` from the first extract only.** Running it means re-running `scripts/ingest_add1.py`.
- **`git_hash` and `clean` moved** from `run_all.py` to `src/report_utils.py`, unchanged, so both scripts share them.
- **Rule 8 items not done here:** AI transcript export is yours to do, and tagging was excluded by your instructions.
