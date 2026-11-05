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

_TBD_

## 6. Gross vs net debt; lease treatment

_TBD_

## 7. Breach thresholds and test frequency

_TBD_

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

## 13. Tax: $	au_{	ext{eff}}$ definition

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

