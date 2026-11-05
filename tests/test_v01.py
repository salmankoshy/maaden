import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from src import analysis, financials, prices, simulate
from src.draws import make_draws

ROOT = Path(__file__).resolve().parents[1]
DT = 1 / 12


def test_a_gbm_zero_vol_deterministic():
    Z = make_draws(100, 12, 1, seed=1)
    mu, S0 = 0.07, 2500.0
    P = prices.simulate_gbm(S0, mu, 0.0, Z, DT)
    t = np.arange(13) * DT
    np.testing.assert_allclose(P, np.broadcast_to(S0 * np.exp(mu * t), P.shape), rtol=1e-12)


def test_b_gbm_mean_matches_analytic():
    n, mu, sigma, S0 = 200_000, 0.05, 0.16, 3000.0
    Z = make_draws(n, 12, 1, seed=42)
    ST = prices.simulate_gbm(S0, mu, sigma, Z, DT)[:, -1]
    se = ST.std(ddof=1) / np.sqrt(n)
    assert abs(ST.mean() - S0 * np.exp(mu * 1.0)) < 4 * se


def test_c_antithetic_rows_are_negatives():
    Z = make_draws(1000, 12, 2, seed=7)
    np.testing.assert_array_equal(Z[500:], -Z[:500])


def test_d_nonpositive_ebitda_is_breach():
    ltm = np.array([[-1.0, 5.0, 5.0, 5.0], [0.0, 5.0, 5.0, 5.0], [5.0, 5.0, 5.0, 5.0]])
    L = financials.leverage(10.0, ltm)
    assert np.isinf(L[0, 0]) and np.isinf(L[1, 0])
    B = analysis.breach(L, np.array([0, 3]), threshold=1e9)
    assert B.tolist() == [True, True, False]


def test_e_no_breach_when_net_debt_nonpositive():
    ltm = np.full((50, 4), 100.0)
    for nd in (0.0, -500.0):
        L = financials.leverage(nd, ltm)
        assert not analysis.breach(L, np.arange(4), threshold=0.0 + 1e-9).any()


@pytest.fixture(scope="module")
def model():
    return simulate.build_model()


def test_f_unit_cost_reproduces_h1_26(model):
    m = model
    pred = financials.al_ebitda(m["pink_cal"], m["b"], m["c"], m["q_cal"], m["fx"])
    assert pred == pytest.approx(m["e_cal"], rel=1e-12)


def test_g_ltm_month12_is_sum_of_months(model):
    rng = np.random.default_rng(0)
    sim = rng.normal(300, 50, size=(20, 12))
    ltm = financials.ltm_series(model["hist"], sim)
    np.testing.assert_allclose(ltm[:, 11], sim.sum(axis=1))
    np.testing.assert_allclose(ltm[:, 0], model["hist"][1:].sum() + sim[:, 0])


def test_h_run_all_is_reproducible():
    path = ROOT / "results" / "results.json"
    outs = []
    for _ in range(2):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_all.py")], check=True, cwd=ROOT,
                       capture_output=True)
        outs.append(json.loads(path.read_text()))
    assert outs[0] == outs[1]
