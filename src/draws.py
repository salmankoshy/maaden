"""Pre-drawn random arrays (common random numbers)."""
import numpy as np


def make_draws(n_paths, n_months, n_factors, seed, antithetic=True):
    """Z with shape (n_paths, n_months, n_factors). With antithetic, rows n/2.. are -Z of rows 0..n/2-1."""
    rng = np.random.default_rng(seed)
    if not antithetic:
        return rng.standard_normal((n_paths, n_months, n_factors))
    if n_paths % 2:
        raise ValueError("n_paths must be even for antithetic pairing")
    half = rng.standard_normal((n_paths // 2, n_months, n_factors))
    return np.concatenate([half, -half], axis=0)
