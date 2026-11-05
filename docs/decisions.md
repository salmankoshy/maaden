# Modeling decisions

## 1. Drift convention (v0.1 zero; v0.2 $\mu=\pi$; historical as sensitivity)

v0.1 uses zero drift (mu = 0, so E[S_t] = S_0): a 12-month credit view should not extrapolate 16 years of aluminium price history. The fitted historical drift is reported in results.json (`mu_hat`); `drift_mode = historical` in assumptions.csv switches it on as a sensitivity. Sigma is the annualized sample volatility of monthly log returns, 2010-01 to the anchor month.

## 2. Real vs nominal (fit real, re-inflate at $\pi$)

_TBD_

## 3. Margin model (unit-cost anchor vs linear regression; back-test)

EBITDA_Al = (b P - c) Q FX, P = Pink Sheet aluminium price. b = realized price / Pink Sheet average over H1-26 (production-weighted realized price); c = b Pbar - EBITDA/(Q FX), Q = H1-26 production. This makes the model reproduce H1-26 EBITDA exactly (test f). Q = production in every period, including the back-test, because FRP is sold separately (FY25: 309 kmt FRP alongside 593 kmt primary sales) and 2026 sales volumes are not disclosed, so production is the only volume measure consistent across periods. c is therefore per tonne produced. Back-test (Q3-25, Q4-25, FY24, FY25, period-average Pink prices, b and c held at H1-26 values) under-predicts actual Al EBITDA by 30-54%: see results.json `backtest`. The H1-26 anchor does not extrapolate to earlier periods, so the unit cost c is not stable; treat model EBITDA levels as anchored to H1-26 only.

## 4. Group aggregation in v0.1 (fixed vs scaled bounds)

Scaling Al alone to group overstates group volatility, and holding everything else fixed understates it. v0.1 reports both. fixed: non-Al LTM held at its actual value to Q2-26 (phosphate + bmnm - corporate = 11,500 SAR m), so group LTM = Al LTM + 11,500 (lower bound on volatility). scaled: group LTM = Al LTM / Al share of group LTM (0.2996), perfect co-movement (upper bound).

## 5. LTM construction from half-year data

Quarterly data exists, so LTM is built from quarters. Before the simulation start (Q3-25..Q2-26), actual quarterly Al EBITDA is spread evenly over the three months of each quarter. Jul-Sep 2026 is not yet reported: the unit-cost model is applied to actual Pink Sheet prices for those months.

Implementation (v0.1): the 12-month history ends at the anchor month (Oct-26). Nov-25..Dec-25 = Q4-25 EBITDA / 3 per month; Jan-Jun 2026 = Q1-26 and Q2-26 / 3; Jul-Oct 2026 (not yet reported) = unit-cost model on actual Pink Sheet prices (Oct-26 included because its price is observed). Simulated months 1..12 are Nov-26..Oct-27; covenant tests at months 3, 6, 9, 12.

## 6. Gross vs net debt; lease treatment

Net debt anchor = 31-Dec-25 audited balance sheet, excluding leases (company definition): borrowings 32,429.42 less cash and equivalents 10,583.55 less time deposits 219.42 = 21,626.45 SAR m. Over FY25 EBITDA 16,159 this is 1.338x, reconciling to the reported 1.3x. Including leases (1,414.85) gives 1.426x; leases are a sensitivity. The H1-26 balance sheet is pending, so the anchor is two quarters stale.

## 7. Breach thresholds and test frequency

Company target range is 2-3x ND/EBITDA (Q1-26 release p1). Covenant levels are not disclosed (FY25 audited FS Note 35.13: covenants exist, in compliance at 31-Dec-25). The working thresholds 2.5x and 3.0x are analyst assumptions, inside and at the top of the target range, and will be reviewed in Phase 2. Test frequency defaults to 3 months.

## 8. Corporate cost treatment

corporate_ebitda is DERIVED, not sourced: sum of Al, phosphate and bmnm segment EBITDA minus group EBITDA, per period (positive = corporate cost / eliminations; Q1-26 group converted from USD at 3.75). Used via its Q3-25..Q2-26 LTM (1,714 SAR m) in `fixed` mode. Checked: non-Al LTM + Al LTM = group LTM exactly.

## 9. OU vs GBM per series (ADF result, half-life CI)

_TBD_

## 10. Correlation on residuals; fit window; 2020-22 stress

_TBD_

## 11. Capex ladders: attributable share, volume linkage, online lag

_TBD_

## 12. Waterfall: $\phi$, $C_{\min}$, refinancing

_TBD_

## 13. Tax: effective rate definition (zakat + tax over profit before zakat and tax)

_TBD_

## 14. Natural hedge: market-linked vs administered input costs

_TBD_

## 15. Disruption scenario parameters and sources

_TBD_

## 16. Collar strike reference (model-implied forward, zero cost)

_TBD_

## 17. Deferral cost definition

_TBD_

## 18. Antithetic CI method; multiplicity correction

Antithetic pairs (Z, -Z): p-hat is the mean of pair means, CI from the sample std of pair means over n/2 pairs, normal approximation (95%). With zero hits the CI is replaced by the rule-of-three bound p < 3/n. No multiplicity correction in v0.1 (two thresholds, reported separately).

## 19. Data gaps

- Phosphate rock 2023-11: missing in the earlier (2025) Pink Sheet release. Left as NaN, not repaired. Series is not a model driver.
- Update (2026 release, retrieved 2026-11-04): the source now reports 347.5 for 2023-11 (same as 2023-10). Value is the World Bank's, not ours; no NaNs remain since 2010-01 in any column. Fetch script keeps NaN as NaN if a gap reappears.

## Input notes (Phase 1a)

- Q2-26 group EBITDA is the rounded headline "SAR 3.9bn" (3,900); the exact figure is not in the release.
- Q1-26 group EBITDA is reported only in USD (964 USD m); converted at the 3.75 peg to 3,615 SAR m in checks. The stored value stays 964 USD m.
- Al volume Q = primary aluminium production, because 2026 sales volumes are not disclosed. For FY25 production (999 kmt) exceeds primary sales (593 kmt; FRP 309 kmt sold separately), so EBITDA per tonne is understated in annual periods; segments.csv uses production in every period for consistency.
- Q2-25 realized price conflict: 2,600 USD/t in the Q2-26 release vs 2,701 in the Q3-25 release (p4). Stored 2,600 (the later release); not used in H1-26 calibration, only in back-tests.
- segments.csv column `segment` uses `aluminum`, `phosphate`, `bmnm` (renamed Gold and Growth Minerals in Q2-26).
- Extract columns `source_url` and `note` are carried into assumptions.csv as extra trailing columns.
- Source PDFs: 3 of 5 downloaded to `source/` (Q2-26 release, Q1-26 release, Integrated Report 2025). The Q4/FY25 and Q3-25 releases on saudiexchange.sa returned HTTP 403 and were not obtained; fetch them manually in a browser.

## 20. Credit core: add1 ingest

`source/maaden_extracted_inputs_add1.csv` (97 rows) is appended to `assumptions.csv` by `scripts/ingest_add1.py`, values as strings, mapped by column name because the source column order differs. Existing rows are unchanged. Scenario settings are separate rows with source `ANALYST`. The four PLACEHOLDER rows are present in the file but no credit code reads them. `scripts/ingest_extracted.py` rebuilds the file from the first extract only, so running it requires re-running `ingest_add1.py`.

## 21. Credit core waterfall

- Net debt = borrowings - cash - time deposits, leases excluded: the company's own definition, and it reproduces the reported 1.3x. Leases-in is reported beside it.
- Annual steps 2026-2030 from the 31-Dec-25 audited balance sheet: it is the last audited base. H1-26 balance sheet is pending.
- Maturities are refinanced: gross debt follows free cash flow only, so a maturity changes nothing in the debt path. Refinancing risk is shown separately in the maturity table, not modeled.
- Cash and time deposits are held constant: all surplus or deficit goes through debt, so net debt moves one-for-one with free cash flow.
- EBITDA flat in nominal SAR with no EBITDA from new capacity: conservative, since capex earns nothing in the horizon. Capex and flat EBITDA are both nominal; no inflation is applied (the inflation row is a PLACEHOLDER and is not read).
- If capex is low enough for D to go negative, interest turns into income at the same rate. Not floored: the tested region has D well above zero, and a floor would add a kink for no benefit.
- +100 bp "floating share only" is a blended rate r + floating share x 1%, with the share held at its 31-Dec-25 value (fixed sukuk share of principal). Applying it to all debt is computed beside it as a bound.
- Breakeven reports the upper end of the bisection bracket, so L_2030 is just above x at that capex. Bracket width is in `credit_capex_search_tol`.
- Tax base uses `tau_eff`, which includes severance fees; FY25 D&A and NCI dividends held flat.
