# Ma'aden Capex Financing Stress Test

## 0. Operating rules

1. I supply every financial input from a filing or dataset. AI scaffolds, never invents numbers. Unknown → placeholder + exact source location to find it.
2. Every input lives in `inputs/assumptions.csv` with columns `key,value,unit,source,date_retrieved`. Code reads from there. No hardcoded numbers in model code.
3. Deterministic: `seed=42` everywhere. Every figure regenerable by one command.
4. Build order is fixed: v0.1 (1 commodity, 1 yr) → v0.2 (3 commodities, 5 yr, capex ladders) → v0.3 (disruptions, policies, CRN) → v1.0 (variance reduction, validation, memo). Never skip ahead.
5. Each phase ends with: tests pass, one PNG, README updated, git tag.
6. Resume/README claims never exceed what the code at that tag does.
7. Timebox. If a phase runs >150% of budget, cut scope per the kill list, don't extend.
8. Plain-language explanation of every modeling choice goes in `docs/decisions.md`. I must be able to defend each in 10 seconds.

Kill list (cut in this order if behind): Arabic summary → dashboard → policies (d)(e) → gold → validation → disruption module. Floor = aluminium + DAP, GBM, 3-yr, 2 policies, antithetic, 6-page report.

Current phase: 0 → 1

Commands: pytest; python scripts/run_all.py
