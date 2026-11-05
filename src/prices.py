"""GBM fit and simulation."""
import numpy as np


def fit_gbm(series, dt):
    """Annualized (mu, sigma) from monthly log returns: sigma^2 = var(r)/dt, mu = mean(r)/dt + sigma^2/2."""
    r = np.diff(np.log(np.asarray(series, dtype=float)))
    sigma2 = r.var(ddof=1) / dt
    return r.mean() / dt + sigma2 / 2.0, np.sqrt(sigma2)


def simulate_gbm(S0, mu, sigma, Z, dt):
    """Exact GBM step. Z: (n_paths, n_months) or (n_paths, n_months, 1). Returns (n_paths, n_months+1)."""
    Z = np.asarray(Z)
    if Z.ndim == 3:
        Z = Z[:, :, 0]
    steps = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    logp = np.concatenate([np.zeros((Z.shape[0], 1)), np.cumsum(steps, axis=1)], axis=1)
    return S0 * np.exp(logp)


def drift_for_mode(mode, mu_hat):
    if mode == "zero":
        return 0.0
    if mode == "historical":
        return mu_hat
    raise ValueError(f"drift_mode {mode!r}")
