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
