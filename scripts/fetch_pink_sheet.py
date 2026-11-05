"""Download World Bank Pink Sheet monthly prices and write inputs/prices_monthly.csv."""
import io
import sys
from pathlib import Path

import pandas as pd
import requests

URL = ("https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
       "related/CMO-Historical-Data-Monthly.xlsx")
SHEET = "Monthly Prices"
HEADER_ROW = 4  # 0-indexed -> sheet row 5
COLUMNS = {
    "Aluminum": "aluminum",
    "DAP": "dap",
    "Phosphate rock": "phosphate_rock",
    "Gold": "gold",
    "Crude oil, Brent": "brent",
}
OUT = Path(__file__).resolve().parents[1] / "inputs" / "prices_monthly.csv"


def main(url=URL):
    resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    raw = pd.read_excel(io.BytesIO(resp.content), sheet_name=SHEET, header=HEADER_ROW)
    raw = raw.rename(columns={raw.columns[0]: "period"})
    raw = raw[raw["period"].astype(str).str.match(r"^\d{4}M\d{2}$")].copy()
    raw["date"] = pd.to_datetime(raw["period"].str.replace("M", "-", regex=False) + "-01")
    missing = [c for c in COLUMNS if c not in raw.columns]
    if missing:
        sys.exit(f"columns not found in sheet: {missing}; got {list(raw.columns)}")
    df = raw[["date"] + list(COLUMNS)].rename(columns=COLUMNS)
    for c in COLUMNS.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")  # '..' placeholders -> NaN
    # No silent repair: source gaps stay NaN (logged in docs/decisions.md).
    for col in COLUMNS.values():
        n = int(df.loc[df["date"] >= "2010-01-01", col].isna().sum())
        if n:
            print(f"NOTE: {col} has {n} NaN row(s) since 2010-01 (left as NaN)")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"last date: {df['date'].iloc[-1]}")
    print(f"wrote {len(df)} rows {df['date'].iloc[0]}..{df['date'].iloc[-1]} -> {OUT}")


if __name__ == "__main__":
    main(*sys.argv[1:])
