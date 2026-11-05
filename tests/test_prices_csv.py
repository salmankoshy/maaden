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


MODEL_COLS = ["aluminum", "dap", "gold"]


def test_no_nans_after_2010_model_columns():
    df = load()
    assert not df.loc[df["date"] >= "2010-01-01", MODEL_COLS].isna().any().any()
