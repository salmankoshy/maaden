# Ma'aden Capex Financing Stress Test

Full plan: see [maaden-build-plan.md](maaden-build-plan.md).

## 0. Operating rules (paste into every chat; also in CLAUDE.md)

1. I supply every financial input from a filing or dataset. AI scaffolds, never invents numbers. Unknown → `NOT_FILLED` + exact source location.
2. Every input lives in `inputs/assumptions.csv` with columns `key,value,unit,period,source,page,date_retrieved`. Code reads from there. No literals in `src/`.
3. No silent data repair. Any gap fill, interpolation or outlier removal is logged in `docs/decisions.md` with a reason, or not done.
4. Deterministic: `seed=42`. All random arrays are pre-drawn once per run and passed to every scenario and policy (common random numbers). One command regenerates every figure.
5. Data snapshots are committed (`prices_monthly.csv`, `cpi_monthly.csv`). `run_all.py` never fetches.
6. Units: internal currency SAR m. Prices in USD per unit (Pink Sheet). FX peg from assumptions. Nominal cash flows; real vs nominal choices stated in `decisions.md`.
7. Build order fixed: v0.1 → v0.2 → v0.3 → v1.0. Never skip ahead.
8. Each phase ends with: tests pass, at least one PNG, README updated, git tag, AI transcripts exported to `docs/ai_transcripts/`.
9. Resume and README claims never exceed what the code at that tag does.
10. Every analytic claim in the report is backed by a test or a simulation number with a CI.
11. Timebox. Phase over 150% of budget → cut per kill list. Never extend.
12. Plain-language reason for every modeling choice in `docs/decisions.md`. Defensible in 10 seconds.

**AI transcripts:** syllabus rule, missing transcript = half grade. Export every Claude Code and claude.ai session the same day.

**Kill list** (cut in this order): Arabic summary → dashboard → policies (d)(e) → jump/bootstrap robustness → gold stochastic (hold gold EBITDA at LTM; never zero it) → OOS validation → disruption module.

**Floor scope** (~25 hrs): Al + DAP stochastic (GBM), gold held at LTM, 3-yr horizon, quarterly LTM leverage test, 2 policies (none, collar), antithetic, 6-page report.

Current phase: 1a (inputs)

Commands: pytest; python scripts/run_all.py
