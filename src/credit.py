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
