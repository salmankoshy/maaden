"""Breach probabilities, percentiles, Jensen gap, back-test."""
import numpy as np
from scipy import stats


def test_columns(n_months, freq):
    """0-based columns of the month-1..n_months arrays that are covenant test dates."""
    return np.arange(freq, n_months + 1, freq) - 1


def breach(L, cols, threshold):
    """Per-path flag: leverage above threshold (inf included) at any test date."""
    return (L[:, cols] > threshold).any(axis=1)


def p_hat(B, ci_level, k):
    """Estimate from antithetic pair means (rows j and j + n/2 are a pair)."""
    B = np.asarray(B, dtype=float)
    n = len(B)
    pair = 0.5 * (B[: n // 2] + B[n // 2:])
    p = pair.mean()
    out = {"p": float(p), "n": int(n), "hits": int(B.sum())}
    if B.sum() == 0:
        out.update(lo=0.0, hi=k / n, zero_hit_bound=k / n)
        return out
    z = stats.norm.ppf(1 - (1 - ci_level) / 2)
    h = z * pair.std(ddof=1) / np.sqrt(len(pair))
    out.update(lo=float(max(p - h, 0.0)), hi=float(min(p + h, 1.0)))
    return out


def percentiles(x, qs):
    return {str(q): float(np.percentile(x, q)) for q in qs}


def jensen(nd, ebitda_ltm):
    """E[L] vs ND/E[EBITDA]; paths with EBITDA <= 0 make E[L] infinite, reported as-is."""
    L = np.where(ebitda_ltm > 0, nd / np.where(ebitda_ltm > 0, ebitda_ltm, 1.0), np.inf)
    return {"E_L": float(L.mean()), "ND_over_E_ebitda": float(nd / ebitda_ltm.mean())}


def backtest_table(rows):
    """rows: dicts with predicted/actual (SAR m); adds error and percent error."""
    out = []
    for r in rows:
        err = r["predicted"] - r["actual"]
        out.append({**r, "error": err, "error_pct": 100 * err / r["actual"]})
    return out
