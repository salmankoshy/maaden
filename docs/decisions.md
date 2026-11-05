# Modeling decisions

## 1. Drift convention (v0.1 zero; v0.2 $\mu=\pi$; historical as sensitivity)

_TBD_

## 2. Real vs nominal (fit real, re-inflate at $\pi$)

_TBD_

## 3. Margin model (unit-cost anchor vs linear regression; back-test)

_TBD_

## 4. Group aggregation in v0.1 (fixed vs scaled bounds)

_TBD_

## 5. LTM construction from half-year data

Quarterly data exists, so LTM is built from quarters. Before the simulation start (Q3-25..Q2-26), actual quarterly Al EBITDA is spread evenly over the three months of each quarter. Jul-Sep 2026 is not yet reported: the unit-cost model is applied to actual Pink Sheet prices for those months.

## 6. Gross vs net debt; lease treatment

Net debt anchor = 31-Dec-25 audited balance sheet, excluding leases (company definition): borrowings 32,429.42 less cash and equivalents 10,583.55 less time deposits 219.42 = 21,626.45 SAR m. Over FY25 EBITDA 16,159 this is 1.338x, reconciling to the reported 1.3x. Including leases (1,414.85) gives 1.426x; leases are a sensitivity. The H1-26 balance sheet is pending, so the anchor is two quarters stale.

## 7. Breach thresholds and test frequency

Company target range is 2-3x ND/EBITDA (Q1-26 release p1). Covenant levels are not disclosed (FY25 audited FS Note 35.13: covenants exist, in compliance at 31-Dec-25). The working thresholds 2.5x and 3.0x are analyst assumptions, inside and at the top of the target range, and will be reviewed in Phase 2. Test frequency defaults to 3 months.

## 8. Corporate cost treatment

_TBD_

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

_TBD_

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
