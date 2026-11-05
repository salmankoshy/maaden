"""Readers for inputs/. Every model number enters the code through here."""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
KMT_TO_T = 1_000.0  # unit conversion for the 'kmt' unit string


class Assumptions:
    def __init__(self, path=None):
        self.df = pd.read_csv(path or INPUTS / "assumptions.csv", dtype=str, keep_default_na=False)

    def row(self, key, period=""):
        m = self.df[(self.df.key == key) & (self.df.period == period)]
        if len(m) != 1:
            raise KeyError(f"assumptions.csv: expected one row for ({key!r}, {period!r}), found {len(m)}")
        r = m.iloc[0]
        if r.value == "NOT_FILLED":
            raise ValueError(f"assumptions.csv: ({key!r}, {period!r}) is NOT_FILLED")
        return r

    def str(self, key, period=""):
        return self.row(key, period).value

    def num(self, key, period=""):
        return float(self.row(key, period).value)

    def list(self, key):
        return [x.strip() for x in self.str(key).split(",")]

    def sar_m(self, key, period):
        """Value in SAR m; USD m rows are converted at the peg."""
        r = self.row(key, period)
        v = float(r.value)
        return v * self.num("fx_sar_per_usd", "peg") if r.unit == "USD m" else v

    def tonnes(self, key, period):
        r = self.row(key, period)
        assert r.unit == "kmt", r.unit
        return float(r.value) * KMT_TO_T


def load_prices(path=None):
    df = pd.read_csv(path or INPUTS / "prices_monthly.csv", parse_dates=["date"])
    return df.set_index("date")


def period_months(period):
    """'Q3-25' / 'FY24' / 'H1-26' -> list of month-start Timestamps."""
    if m := re.fullmatch(r"Q([1-4])-(\d\d)", period):
        q, yy = int(m[1]), 2000 + int(m[2])
        return [pd.Timestamp(yy, 3 * (q - 1) + k, 1) for k in (1, 2, 3)]
    if m := re.fullmatch(r"FY(\d\d)", period):
        return [pd.Timestamp(2000 + int(m[1]), k, 1) for k in range(1, 13)]
    if m := re.fullmatch(r"H1-(\d\d)", period):
        return [pd.Timestamp(2000 + int(m[1]), k, 1) for k in range(1, 7)]
    raise ValueError(period)


def mean_price(prices, period, col="aluminum"):
    return float(prices.loc[period_months(period), col].mean())
