"""Deterministic credit core: FY25 credit metrics and the 2026-2030 annual debt waterfall (SAR m)."""
import numpy as np

from src.financials import leverage
from src.inputs import Assumptions

BP_PER_UNIT = 10_000.0  # unit conversion for the 'bp' unit string
BS = "31-Dec-25"
FY = "FY25"
MATURITY_YEARS = ["2026", "2027", "2028", "2029", "2030", "2031+"]
MULTIPLIERS = ["flat", "minus10", "minus20"]
THRESHOLDS = ["low", "high"]


def load_inputs(a=None):
    """Every input the credit core uses. PLACEHOLDER rows are not read."""
    a = a or Assumptions()
    return {
        "ebitda": a.sar_m("group_ebitda", FY),
        "borrowings": a.num("total_borrowings", BS),
        "leases": a.num("lease_liabilities", BS),
        "cash": a.num("cash_and_equivalents", BS),
        "time_deposits": a.num("time_deposits", BS),
        "undrawn": a.num("undrawn_facilities", BS),
        "interest_borrowings": a.num("interest_expense_borrowings", FY),
        "finance_cost": a.num("finance_cost", FY),
        "principal": a.num("debt_principal_total", BS),
        "sukuk": a.num("sukuk_fixed_principal", BS),
        "maturities": {y: a.num("debt_maturity_principal", y) for y in MATURITY_YEARS},
        "r": a.num("effective_interest_rate", FY),
        "tau": a.num("tau_eff", FY),
        "da": a.num("da_total", FY),
        "nci": a.num("dividends_to_nci_fy25", FY),
        "capex_guidance": a.num("capex_guidance_2026", "FY26"),
        "shock_bp": a.num("credit_rate_shock_bp"),
        "years": list(range(int(a.num("credit_first_year")), int(a.num("credit_last_year")) + 1)),
        "multipliers": {k: a.num("credit_ebitda_multiplier", k) for k in MULTIPLIERS},
        "thresholds": {k: a.num("credit_threshold", k) for k in THRESHOLDS},
        "search": (a.num("credit_capex_search_low"), a.num("credit_capex_search_high"),
                   a.num("credit_capex_search_tol")),
    }


def floating_share(inp):
    return 1 - inp["sukuk"] / inp["principal"]


def metrics(inp):
    """FY25 credit metrics. ND excludes leases (company definition)."""
    e = inp["ebitda"]
    liquid = inp["cash"] + inp["time_deposits"]
    nd = inp["borrowings"] - liquid
    nd_leases = nd + inp["leases"]
    floating = floating_share(inp)
    return {
        "net_debt": nd,
        "net_debt_incl_leases": nd_leases,
        "leverage": nd / e,
        "leverage_incl_leases": nd_leases / e,
        "ebitda_cushion": {k: 1 - nd / (x * e) for k, x in inp["thresholds"].items()},
        "interest_cover_borrowings": e / inp["interest_borrowings"],
        "interest_cover_finance_cost": e / inp["finance_cost"],
        "liquidity": liquid + inp["undrawn"],
        "floating_share": floating,
        "rate_shock_cost": floating * inp["principal"] * inp["shock_bp"] / BP_PER_UNIT,
    }


def maturity_table(inp):
    return [{"year": y, "principal": v, "share": v / inp["principal"]} for y, v in inp["maturities"].items()]


def shocked_rate(inp, shock="none"):
    """All-in rate. 'floating': shock on the floating share only (blended rate). 'all': shock on all debt."""
    bump = inp["shock_bp"] / BP_PER_UNIT
    return inp["r"] + {"none": 0.0, "floating": floating_share(inp) * bump, "all": bump}[shock]


def waterfall(ebitda, capex, inp, rate=None):
    """Debt roll-forward. ebitda: scalar or array whose last axis is years. Maturities are refinanced: gross debt
    moves with free cash flow only. Cash and time deposits stay constant. L is +inf when EBITDA <= 0."""
    r = inp["r"] if rate is None else rate
    n = len(inp["years"])
    E = np.broadcast_to(np.asarray(ebitda, dtype=float), np.shape(ebitda)[:-1] + (n,)
                        if np.ndim(ebitda) else (n,))
    liquid = inp["cash"] + inp["time_deposits"]
    D = np.empty(E.shape[:-1] + (n + 1,))
    D[..., 0] = inp["borrowings"]
    interest, tax, fcf = np.empty(E.shape), np.empty(E.shape), np.empty(E.shape)
    for t in range(n):
        interest[..., t] = r * D[..., t]
        tax[..., t] = inp["tau"] * np.maximum(E[..., t] - inp["da"] - interest[..., t], 0)
        fcf[..., t] = E[..., t] - interest[..., t] - tax[..., t] - capex - inp["nci"]
        D[..., t + 1] = D[..., t] - fcf[..., t]
    return {"E": E, "D": D, "interest": interest, "tax": tax, "fcf": fcf, "L": leverage(D[..., 1:] - liquid, E)}


def bisect_capex(crossed, search):
    """Smallest capex (within tol) where crossed(capex) is true; assumes crossed is monotone in capex."""
    lo, hi, tol = search
    if crossed(lo) or not crossed(hi):
        raise ValueError(f"no crossing inside capex search range {search}")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if crossed(mid) else (mid, hi)
    return hi


def breakeven(inp, multiplier, x, rate=None):
    """Capex at which L_2030 first exceeds x, with the first year L > x at that capex."""
    E = multiplier * inp["ebitda"]
    capex = bisect_capex(lambda c: waterfall(E, c, inp, rate)["L"][-1] > x, inp["search"])
    L = waterfall(E, capex, inp, rate)["L"]
    return {"capex": capex, "first_breach_year": inp["years"][int(np.argmax(L > x))], "L_path": L.tolist()}


def breakeven_table(inp):
    rows = []
    for mk, m in inp["multipliers"].items():
        for tk, x in inp["thresholds"].items():
            base = breakeven(inp, m, x)
            shocked = breakeven(inp, m, x, shocked_rate(inp, "floating"))
            all_debt = breakeven(inp, m, x, shocked_rate(inp, "all"))
            rows.append({"scenario": mk, "multiplier": m, "threshold": x, "breakeven_capex": base["capex"],
                         "first_breach_year": base["first_breach_year"],
                         "breakeven_capex_shock_floating": shocked["capex"],
                         "first_breach_year_shock_floating": shocked["first_breach_year"],
                         "breakeven_capex_shock_all_debt": all_debt["capex"]})
    return rows
