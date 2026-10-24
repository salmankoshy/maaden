from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parents[1] / "inputs" / "prices_monthly.csv"
COLS = ["date", "aluminum", "dap", "phosphate_rock", "gold", "brent"]


def load():
    return pd.read_csv(CSV)


def test_columns():
    assert list(load().columns) == COLS


def test_row_count():
    assert len(load()) >= 150


def test_iso_dates():
    d = pd.to_datetime(load()["date"], format="%Y-%m-%d")
    assert d.is_monotonic_increasing


def test_no_nans_after_2010():
    df = load()
    assert not df[df["date"] >= "2010-01-01"].isna().any().any()
