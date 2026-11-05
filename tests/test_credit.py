import numpy as np
import pytest

from src import credit


@pytest.fixture(scope="module")
def inp():
    return credit.load_inputs()


def test_net_debt_and_leverage(inp):
    m = credit.metrics(inp)
    assert m["net_debt"] == pytest.approx(21626.45, abs=1e-6)
    assert m["leverage"] == pytest.approx(1.338, abs=0.001)
    assert m["net_debt_incl_leases"] == pytest.approx(21626.45 + 1414.85, abs=1e-6)


def test_cushions(inp):
    c = credit.metrics(inp)["ebitda_cushion"]
    assert c["low"] == pytest.approx(0.4647, abs=0.0001)
    assert c["high"] == pytest.approx(0.5539, abs=0.0001)


def test_cover_and_liquidity(inp):
    m = credit.metrics(inp)
    assert m["interest_cover_borrowings"] == pytest.approx(8.756, abs=0.001)
    assert m["liquidity"] == pytest.approx(25252.97, abs=1e-6)


def test_rate_sensitivity(inp):
    m = credit.metrics(inp)
    assert round(m["floating_share"], 4) == 0.8259
    assert m["rate_shock_cost"] == pytest.approx(268.7, abs=0.1)


def test_maturity_profile(inp):
    t = credit.maturity_table(inp)
    assert sum(r["principal"] for r in t) == pytest.approx(inp["principal"], abs=1e-6)
    assert round(next(r for r in t if r["year"] == "2030")["share"], 4) == 0.2343


def test_placeholders_not_read(inp):
    """No credit input may come from a PLACEHOLDER row."""
    from src.inputs import Assumptions
    used = Assumptions()
    bad = used.df[used.df.source.str.contains("PLACEHOLDER")]
    assert set(bad.key) == {"capex_ladder_base_annual", "pi_expected_inflation", "cash_floor_c_min",
                            "repay_share_phi"}
    src = open(credit.__file__, encoding="utf-8").read()
    assert not any(k in src for k in bad.key)


def test_waterfall_first_year_by_hand(inp):
    capex = inp["capex_guidance"]
    w = credit.waterfall(inp["ebitda"], capex, inp)
    interest = inp["r"] * inp["borrowings"]
    tax = inp["tau"] * (inp["ebitda"] - inp["da"] - interest)
    fcf = inp["ebitda"] - interest - tax - capex - inp["nci"]
    assert w["D"][1] == pytest.approx(inp["borrowings"] - fcf, rel=1e-12)
    assert w["L"][0] == pytest.approx((w["D"][1] - inp["cash"] - inp["time_deposits"]) / inp["ebitda"], rel=1e-12)


def test_tax_floor_at_zero(inp):
    w = credit.waterfall(inp["da"] * 0.5, 0.0, inp)
    assert (w["tax"] == 0).all()


@pytest.mark.parametrize("mult,x,want", [("flat", "high", 17113), ("minus10", "high", 14855),
                                         ("minus20", "high", 12596), ("flat", "low", 15639)])
def test_breakeven_targets(inp, mult, x, want):
    b = credit.breakeven(inp, inp["multipliers"][mult], inp["thresholds"][x])
    assert b["capex"] == pytest.approx(want, abs=5)
    assert b["L_path"][-1] >= inp["thresholds"][x]


def test_rate_shock_breakevens(inp):
    m, x = inp["multipliers"]["flat"], inp["thresholds"]["high"]
    base = credit.breakeven(inp, m, x)["capex"]
    all_debt = credit.breakeven(inp, m, x, credit.shocked_rate(inp, "all"))["capex"]
    floating = credit.breakeven(inp, m, x, credit.shocked_rate(inp, "floating"))["capex"]
    assert all_debt == pytest.approx(16755, abs=5)
    assert all_debt < floating < base


def test_zero_capex_debt_non_increasing(inp):
    w = credit.waterfall(inp["ebitda"], 0.0, inp)
    assert (w["fcf"] > 0).all()
    assert (np.diff(w["D"]) <= 0).all()


def test_leverage_monotone_in_capex(inp):
    capex = np.linspace(*inp["search"][:2], 200)
    L = [credit.waterfall(inp["ebitda"], c, inp)["L"][-1] for c in capex]
    assert (np.diff(L) > 0).all()


def test_first_breach_year_is_in_horizon(inp):
    for r in credit.breakeven_table(inp):
        assert r["first_breach_year"] in inp["years"]


def test_nonpositive_ebitda_is_infinite_leverage(inp):
    assert np.isinf(credit.waterfall(0.0, 0.0, inp)["L"]).all()
