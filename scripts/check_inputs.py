"""Phase 1a sanity checks on inputs/assumptions.csv. Exits non-zero on failure; never repairs data."""
import sys
from pathlib import Path

import pandas as pd

A = pd.read_csv(Path(__file__).resolve().parents[1] / "inputs" / "assumptions.csv", dtype=str)


def v(key, period=None):
    m = A[(A.key == key) & ((A.period == period) if period else True)]
    assert len(m) == 1, (key, period, len(m))
    return float(m.value.iloc[0])


fx = v("fx_sar_per_usd")
checks = []

# 1. ND ex-leases (31-Dec-25) / FY25 EBITDA vs reported
nd = v("total_borrowings", "31-Dec-25") - v("cash_and_equivalents", "31-Dec-25") - v("time_deposits", "31-Dec-25")
lev = nd / v("group_ebitda", "FY25")
nd_incl = nd + v("lease_liabilities", "31-Dec-25")
checks.append(("ND ex-leases / FY25 EBITDA ~1.34x (reported 1.3x)", lev, 1.33 <= lev <= 1.35))
print(f"  incl. leases (sensitivity): {nd_incl / v('group_ebitda', 'FY25'):.3f}x; ND ex-leases = {nd:,.2f}")

# 2. LTM group EBITDA to Q2-26 (Q1-26 converted from USD at peg)
q1_26 = v("group_ebitda", "Q1-26") * fx
ltm = v("group_ebitda", "Q3-25") + v("group_ebitda", "Q4-25") + q1_26 + v("group_ebitda", "Q2-26")
checks.append(("LTM group EBITDA to Q2-26 ~16,420", ltm, abs(ltm - 16420) <= 1))

# 3. Al unit cost from H1-26, Q = production, realized price production-weighted
q = {p: v("al_production_kmt", p) for p in ("Q1-26", "Q2-26")}
pr = {p: v("al_realized_usd_t", p) for p in q}
e = v("al_ebitda", "Q1-26") + v("al_ebitda", "Q2-26")
qq = sum(q.values())
pbar = sum(pr[p] * q[p] for p in q) / qq
c = pbar - (e * 1e6) / (qq * 1e3 * fx)
rep = [v("al_cost_per_t_usd", p) for p in q]
checks.append((f"Al unit cost H1-26 ~2,208 (reported {min(rep):.0f}-{max(rep):.0f})", c,
               abs(c - 2208) <= 2 and min(rep) - 5 <= c <= max(rep) + 5))

# informational
print("  segment sum minus group (corporate gap, SAR m):")
for p in ("Q2-26", "Q1-26", "Q4-25", "Q3-25", "Q2-25", "FY25"):
    g = v("group_ebitda", p) * (fx if p == "Q1-26" else 1)
    s = v("al_ebitda", p) + v("phosphate_ebitda", p) + v("bmnm_ebitda", p)
    print(f"    {p}: {s - g:,.0f}")
q1_25 = v("group_ebitda", "Q1-25") + v("group_ebitda", "Q2-25") + v("group_ebitda", "Q3-25") + v("group_ebitda", "Q4-25")
print(f"  FY25 = sum of quarters? {q1_25:,.0f} vs {v('group_ebitda','FY25'):,.0f}")

ok = True
for name, val, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'}  {name}: {val:,.4f}")
    ok &= passed
sys.exit(0 if ok else 1)
