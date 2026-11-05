"""Credit core results: results/credit.json, results/tables/*.csv, Excel model, figures. Never fetches data."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import credit, credit_xlsx, plots  # noqa: E402
from src.inputs import Assumptions  # noqa: E402
from src.report_utils import clean, git_hash  # noqa: E402

RES = ROOT / "results"


def write_csv(rows, name):
    (RES / "tables").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(RES / "tables" / name, index=False, lineterminator="\n")


def waterfall_table(inp, capex):
    w = credit.waterfall(inp["ebitda"], capex, inp)
    return [{"year": y, "ebitda": w["E"][t], "interest": w["interest"][t], "tax": w["tax"][t], "capex": capex,
             "nci_dividends": inp["nci"], "fcf": w["fcf"][t], "debt": w["D"][t + 1], "leverage": w["L"][t]}
            for t, y in enumerate(inp["years"])]


def build():
    inp = credit.load_inputs()
    return {
        "git_hash": git_hash(),
        "base": {"balance_sheet": credit.BS, "ebitda_period": credit.FY, "ebitda": inp["ebitda"],
                 "r": inp["r"], "r_shock_floating": credit.shocked_rate(inp, "floating"),
                 "r_shock_all": credit.shocked_rate(inp, "all"), "tau": inp["tau"], "da": inp["da"],
                 "nci": inp["nci"], "capex_guidance_2026": inp["capex_guidance"],
                 "thresholds": inp["thresholds"], "multipliers": inp["multipliers"],
                 "shock_bp": inp["shock_bp"]},
        "metrics": credit.metrics(inp),
        "maturities": credit.maturity_table(inp),
        "breakeven": credit.breakeven_table(inp),
        "waterfall_at_guidance": waterfall_table(inp, inp["capex_guidance"]),
    }


def write_outputs(out):
    m = out["metrics"]
    flat = {k: v for k, v in m.items() if not isinstance(v, dict)}
    flat.update({f"ebitda_cushion_{k}": v for k, v in m["ebitda_cushion"].items()})
    write_csv([{"metric": k, "value": v} for k, v in flat.items()], "credit_metrics.csv")
    write_csv(out["breakeven"], "credit_breakeven.csv")
    write_csv(out["maturities"], "credit_maturities.csv")
    write_csv(out["waterfall_at_guidance"], "credit_waterfall_guidance.csv")
    with open(RES / "credit.json", "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(clean(out), indent=2, sort_keys=True) + "\n")


def breakeven_chart(inp, table):
    a = Assumptions()
    capex = np.arange(a.num("credit_chart_capex_low"), a.num("credit_chart_capex_high") + a.num("credit_chart_capex_step"),
                      a.num("credit_chart_capex_step"))
    curves, points = {}, []
    for i, (k, m) in enumerate(inp["multipliers"].items()):
        curves[f"x{m:.1f}"] = np.array([credit.waterfall(m * inp["ebitda"], c, inp)["L"][-1] for c in capex])
        points += [(i, r["breakeven_capex"], r["threshold"]) for r in table if r["scenario"] == k]
    (RES / "figures").mkdir(parents=True, exist_ok=True)
    plots.credit_breakeven(capex, curves, sorted(inp["thresholds"].values()),
                           (a.num("target_nd_ebitda_low", "policy"), a.num("target_nd_ebitda_high", "policy")),
                           inp["capex_guidance"], points, RES / "figures" / "credit_breakeven.png")


def main():
    out = build()
    write_outputs(out)
    credit_xlsx.build(RES / "maaden_credit_model.xlsx", credit.load_inputs(), out["breakeven"])
    breakeven_chart(credit.load_inputs(), out["breakeven"])
    print(f"wrote {RES / 'credit.json'} and credit tables")
    return out


if __name__ == "__main__":
    main()
