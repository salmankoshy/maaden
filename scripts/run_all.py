"""One command -> results/results.json + results/figures/v01_hist.png. Never fetches data."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src import analysis, plots, simulate  # noqa: E402


def git_hash():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return "inf" if np.isinf(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def main():
    m = simulate.build_model()
    a = m["a"]
    res = simulate.run(m)
    n_paths = res["P"].shape[0]
    n_months = int(a.num("sim_n_months"))
    freq = int(a.num("covenant_test_freq_months"))
    ci, k = a.num("ci_level"), a.num("zero_hit_bound_k")
    qs = [float(x) for x in a.list("percentiles")]
    thresholds = {"low": a.num("breach_threshold_low"), "high": a.num("breach_threshold_high")}
    cols_q = analysis.test_columns(n_months, freq)
    cols_a = analysis.test_columns(n_months, int(m["mpy"]))
    cur = simulate.current_leverage(m)

    modes = {}
    for mode, d in res["mode"].items():
        L, g = d["L"], d["ltm"]
        modes[mode] = {
            "breach_quarterly_test": {n: analysis.p_hat(analysis.breach(L, cols_q, t), ci, k)
                                      for n, t in thresholds.items()},
            "breach_annual_test": {n: analysis.p_hat(analysis.breach(L, cols_a, t), ci, k)
                                   for n, t in thresholds.items()},
            "leverage_month12_percentiles": analysis.percentiles(L[:, -1], qs),
            "group_ltm_ebitda_month12_percentiles": analysis.percentiles(g[:, -1], qs),
            "jensen_month12": analysis.jensen(m["nd"], g[:, -1]),
            "current_leverage": cur[mode],
        }

    out = {
        "seed": int(a.num("sim_seed")), "n_paths": n_paths, "n_months": n_months,
        "git_hash": git_hash(), "anchor_date": str(m["anchor"].date()),
        "thresholds": thresholds, "test_freq_months": freq,
        "price": {"S0_usd_t": m["S0"], "mu_hat": m["mu_hat"], "mu_used": m["mu"], "sigma": m["sigma"],
                  "drift_mode": a.str("drift_mode"), "n_fit_obs": m["n_fit"]},
        "calibration": {"basis_b": m["b"], "unit_cost_c_usd_t": m["c"], "pink_avg_h1_26": m["pink_cal"],
                        "realized_avg_h1_26": m["realized_cal"], "production_h1_26_t": m["q_cal"],
                        "al_ebitda_h1_26_sar_m": m["e_cal"], "monthly_volume_t": m["q_month"]},
        "anchors": {"net_debt_sar_m": m["nd"], "al_actual_ltm_q2_26": m["al_actual_ltm"],
                    "group_actual_ltm_q2_26": m["group_actual_ltm"], "nonal_ltm": m["nonal_ltm"],
                    "al_share": m["al_share"], "al_ltm_at_anchor": cur["al_ltm_at_anchor"],
                    "history_months": [str(x.date()) for x in m["hist_months"]],
                    "history_al_ebitda_sar_m": list(m["hist"])},
        "current_leverage": {k_: v for k_, v in cur.items() if k_ != "al_ltm_at_anchor"},
        "modes": modes,
        "backtest": simulate.backtest(m),
    }
    res_dir = ROOT / "results"
    (res_dir / "figures").mkdir(parents=True, exist_ok=True)
    (res_dir / "results.json").write_text(json.dumps(clean(out), indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8", newline="\n")
    plots.hist_leverage({k_: v["L"][:, -1] for k_, v in res["mode"].items()},
                        list(thresholds.values()), {k_: cur[k_] for k_ in res["mode"]},
                        res_dir / "figures" / "v01_hist.png", clip_max=thresholds["high"] * 2)
    print(f"wrote {res_dir / 'results.json'} and figures/v01_hist.png")
    return out


if __name__ == "__main__":
    main()
