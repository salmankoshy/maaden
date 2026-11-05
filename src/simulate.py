"""Orchestration: calibrate from inputs, simulate Al prices, build LTM leverage in both aggregation modes."""
import numpy as np
import pandas as pd

from . import analysis, financials, prices as pr
from .draws import make_draws
from .inputs import Assumptions, load_prices, mean_price, period_months

MODES = ("fixed", "scaled")


def build_model(a=None, px=None):
    """Everything deterministic that the simulation needs, derived from inputs/."""
    a = a or Assumptions()
    px = px if px is not None else load_prices()
    fx = a.num("fx_sar_per_usd", "peg")
    mpy = a.num("months_per_year")
    anchor = pd.Timestamp(a.str("price_anchor_date"))

    # --- calibration on H1-26: Q = production, b from realized vs Pink Sheet, c from EBITDA
    cq = a.list("calib_quarters")
    q_t = sum(a.tonnes("al_production_kmt", p) for p in cq)
    realized = sum(a.num("al_realized_usd_t", p) * a.tonnes("al_production_kmt", p) for p in cq) / q_t
    pink = float(np.mean([px.loc[m, "aluminum"] for p in cq for m in period_months(p)]))
    e_cal = sum(a.sar_m("al_ebitda", p) for p in cq)
    b, c = financials.calibrate(realized, pink, e_cal, q_t, fx)
    n_cal_months = sum(len(period_months(p)) for p in cq)
    q_month = q_t / n_cal_months

    # --- 12-month history ending at the anchor
    hist_months = list(pd.date_range(end=anchor, periods=int(mpy), freq="MS"))
    reported = set(a.list("ltm_hist_quarters"))
    month_to_q = {m: p for p in reported for m in period_months(p)}
    hist = []
    for m in hist_months:
        if m in month_to_q:
            p = month_to_q[m]
            hist.append(a.sar_m("al_ebitda", p) / len(period_months(p)))
        else:  # not yet reported: unit-cost model on the actual Pink Sheet price
            hist.append(float(financials.al_ebitda(px.loc[m, "aluminum"], b, c, q_month, fx)))
    hist = np.array(hist)

    # --- actual LTM to last reported quarter (fixed/scaled anchors)
    rq = a.list("ltm_hist_quarters")
    al_actual = sum(a.sar_m("al_ebitda", p) for p in rq)
    group_actual = sum(a.sar_m("group_ebitda", p) for p in rq)
    nonal = sum(a.sar_m("phosphate_ebitda", p) + a.sar_m("bmnm_ebitda", p) - a.sar_m("corporate_ebitda", p)
                for p in rq)
    assert abs(nonal + al_actual - group_actual) < 1e-6, (nonal, al_actual, group_actual)

    # --- net debt: audited anchor balance sheet, ex-leases (company definition)
    ap = a.str("nd_anchor_period")
    nd = a.num("total_borrowings", ap) - a.num("cash_and_equivalents", ap) - a.num("time_deposits", ap)

    # --- GBM fit
    fit = px.loc[pd.Timestamp(a.str("price_fit_start")):anchor, "aluminum"]
    dt = 1.0 / mpy
    mu_hat, sigma = pr.fit_gbm(fit.values, dt)
    mu = pr.drift_for_mode(a.str("drift_mode"), mu_hat)

    return dict(a=a, px=px, fx=fx, mpy=mpy, dt=dt, anchor=anchor, b=b, c=c, q_month=q_month, q_cal=q_t,
                pink_cal=pink, realized_cal=realized, e_cal=e_cal, hist=hist, hist_months=hist_months,
                al_actual_ltm=al_actual, group_actual_ltm=group_actual, nonal_ltm=nonal,
                al_share=al_actual / group_actual, nd=nd, mu_hat=mu_hat, mu=mu, sigma=sigma,
                S0=float(px.loc[anchor, "aluminum"]), n_fit=len(fit))


def run(m, n_paths=None, seed=None, antithetic=True, Z=None):
    """Simulate. Returns dict with price paths, Al LTM, and per-mode group LTM and leverage (n_paths, n_months)."""
    a = m["a"]
    n_paths = n_paths or int(a.num("sim_n_paths"))
    seed = a.num("sim_seed") if seed is None else seed
    n_months = int(a.num("sim_n_months"))
    if Z is None:
        Z = make_draws(n_paths, n_months, 1, int(seed), antithetic)
    P = pr.simulate_gbm(m["S0"], m["mu"], m["sigma"], Z, m["dt"])
    al_m = financials.al_ebitda(P[:, 1:], m["b"], m["c"], m["q_month"], m["fx"])
    al_ltm = financials.ltm_series(m["hist"], al_m)
    out = {"P": P, "al_ltm": al_ltm, "mode": {}}
    for mode in MODES:
        g = financials.group_ebitda_ltm(al_ltm, mode, m["nonal_ltm"], m["al_share"])
        out["mode"][mode] = {"ltm": g, "L": financials.leverage(m["nd"], g)}
    return out


def current_leverage(m):
    """Leverage at t=0 (LTM to the anchor month) in each mode, plus the reported-basis LTM to Q2-26."""
    al0 = m["hist"].sum()
    return {
        "fixed": float(financials.leverage(m["nd"], al0 + m["nonal_ltm"])),
        "scaled": float(financials.leverage(m["nd"], al0 / m["al_share"])),
        "reported_basis_ltm_q2_26": float(financials.leverage(m["nd"], m["group_actual_ltm"])),
        "al_ltm_at_anchor": float(al0),
    }


def backtest(m):
    """Unit-cost model at the period-average Pink Sheet price vs actual Al EBITDA; Q = production."""
    a, px = m["a"], m["px"]
    rows = []
    for p in a.list("backtest_periods"):
        pbar = mean_price(px, p)
        q = a.tonnes("al_production_kmt", p)
        pred = float(financials.al_ebitda(pbar, m["b"], m["c"], q, m["fx"]))
        rows.append({"period": p, "pink_avg_usd_t": pbar, "production_t": q,
                     "predicted": pred, "actual": a.sar_m("al_ebitda", p)})
    return analysis.backtest_table(rows)
