"""Evaluates the workbook's formulas with a small Python evaluator and compares to src/credit.py.
This checks formula logic and references; it is not a spreadsheet-engine recalculation."""
import re

import numpy as np
import pytest
from openpyxl import load_workbook

from src import credit, credit_xlsx

REF = re.compile(r"(?:(\w+)!)?\$?\b([A-Z]{1,2})\$?(\d+)\b(?::\$?([A-Z]{1,2})\$?(\d+))?")


class Evaluator:
    def __init__(self, wb):
        self.wb, self.cache = wb, {}

    def get(self, sheet, col, row):
        key = (sheet, col, row)
        if key not in self.cache:
            v = self.wb[sheet][f"{col}{row}"].value
            self.cache[key] = self.formula(v, sheet) if isinstance(v, str) and v.startswith("=") else v
        return self.cache[key]

    def formula(self, text, sheet):
        def sub(m):
            s = m[1] or sheet
            if m[4]:
                return "[" + ",".join(repr(self.get(s, m[2], r)) for r in range(int(m[3]), int(m[5]) + 1)) + "]"
            return repr(self.get(s, m[2], int(m[3])))
        env = {"MAX": max, "SUM": sum, "IF": lambda c, a, b: a if c else b}
        return eval(REF.sub(sub, text[1:]), {"__builtins__": {}}, env)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    inp = credit.load_inputs()
    path = tmp_path_factory.mktemp("x") / "m.xlsx"
    credit_xlsx.build(path, inp, credit.breakeven_table(inp))
    return inp, load_workbook(path)


def test_metrics_formulas_match_python(built):
    inp, wb = built
    ev, m = Evaluator(wb), credit.metrics(inp)
    py = {**{k: v for k, v in m.items() if not isinstance(v, dict)},
          **{f"ebitda_cushion_{k}": v for k, v in m["ebitda_cushion"].items()}}
    names = {wb["Metrics"][f"A{i}"].value: i for i in range(3, wb["Metrics"].max_row + 1)}
    assert set(names) == set(py)
    for k, i in names.items():
        assert ev.get("Metrics", "B", i) == pytest.approx(py[k], abs=0.01), k


@pytest.mark.parametrize("capex", [None, 9000.0, 21000.0])
def test_waterfall_formulas_match_python(built, capex):
    inp, wb = built
    c = inp["capex_guidance"] if capex is None else capex
    wb["Waterfall"][credit_xlsx.CAPEX_CELL].value = c
    ev = Evaluator(wb)
    w = credit.waterfall(inp["ebitda"], c, inp)
    rows = {wb["Waterfall"][f"A{i}"].value: i for i in range(7, 16)}
    py = {"Interest": w["interest"], "Tax": w["tax"], "FCF": w["fcf"], "Gross debt": w["D"][1:], "Leverage (x)": w["L"]}
    for name, arr in py.items():
        got = [ev.get("Waterfall", col, rows[name]) for col in "CDEFG"]
        np.testing.assert_allclose(got, arr, atol=0.01, err_msg=name)
    wb["Waterfall"][credit_xlsx.CAPEX_CELL].value = inp["capex_guidance"]


def test_maturities_sum_to_principal(built):
    inp, wb = built
    ev = Evaluator(wb)
    assert ev.get("Maturities", "B", 9) == pytest.approx(inp["principal"], abs=0.01)
    assert ev.get("Maturities", "C", 7) == pytest.approx(0.2343, abs=0.0001)


def test_sheet_contract(built):
    inp, wb = built
    assert wb.sheetnames[:5] == ["Inputs", "Metrics", "Waterfall", "Breakeven", "Maturities"]
    ws = wb["Waterfall"]
    assert ws[credit_xlsx.CAPEX_CELL].value == inp["capex_guidance"]
    assert ws[credit_xlsx.CAPEX_CELL].fill.fgColor.rgb.endswith("FFFF00")
    assert ws["C3"].value == credit_xlsx.CAPEX_LABEL
    src = [str(r[4].value) for r in wb["Inputs"].iter_rows(min_row=3)]
    assert not any("PLACEHOLDER" in s for s in src)
    assert "ANALYST" in src
    assert "Python" in wb["Breakeven"]["A1"].value


def test_only_known_functions(built):
    _, wb = built
    for ws in wb:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    assert set(re.findall(r"([A-Z]+)\(", c.value)) <= {"MAX", "SUM", "IF"}, c.coordinate
