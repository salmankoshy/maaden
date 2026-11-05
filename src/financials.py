"""Aluminium unit-cost EBITDA, LTM construction, group aggregation, leverage."""
import numpy as np


def calibrate(realized_pbar, pink_pbar, ebitda_sar_m, q_tonnes, fx):
    """Basis b = realized / Pink Sheet; unit cost c = b*Pbar - EBITDA/(Q*FX) (USD per tonne produced)."""
    b = realized_pbar / pink_pbar
    c = b * pink_pbar - ebitda_sar_m * 1e6 / (q_tonnes * fx)
    return b, c


def al_ebitda(P, b, c, q_tonnes, fx):
    """EBITDA in SAR m for volume q_tonnes at USD/t price P."""
    return (b * np.asarray(P) - c) * q_tonnes * fx / 1e6


def ltm_series(hist_monthly, sim_monthly):
    """LTM at sim months 1..n. hist_monthly: (w,) months ending at the anchor; sim_monthly: (n_paths, n)."""
    n_paths, n = sim_monthly.shape
    w = len(hist_monthly)
    x = np.concatenate([np.broadcast_to(hist_monthly, (n_paths, w)), sim_monthly], axis=1)
    cs = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(x, axis=1)], axis=1)
    idx = np.arange(1, n + 1)
    return cs[:, idx + w] - cs[:, idx]


def group_ebitda_ltm(al_ltm, mode, nonal_ltm, al_share):
    """fixed: other segments and corporate held at actual LTM. scaled: Al LTM / Al share of group LTM."""
    if mode == "fixed":
        return al_ltm + nonal_ltm
    if mode == "scaled":
        return al_ltm / al_share
    raise ValueError(mode)


def leverage(nd, ebitda_ltm):
    """nd / ebitda_ltm; +inf when ebitda_ltm <= 0 (breach)."""
    e = np.asarray(ebitda_ltm, dtype=float)
    return np.where(e > 0, nd / np.where(e > 0, e, 1.0), np.inf)
