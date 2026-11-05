"""Excel export of the credit core. Metrics, Waterfall and Maturities are live formulas on the Inputs sheet."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from src.credit import BP_PER_UNIT, BS, FY, MATURITY_YEARS, MULTIPLIERS, THRESHOLDS
from src.inputs import Assumptions

FONT = "Arial"
BLACK, BLUE, GREEN = "000000", "0000FF", "008000"
YELLOW = PatternFill("solid", fgColor="FFFF00")
HEAD_FILL = PatternFill("solid", fgColor="E7E6E6")
NUM, TIMES, PCT = "#,##0.00;(#,##0.00);-", '0.000"x"', "0.0%"

INPUT_ROWS = [("group_ebitda", FY), ("total_borrowings", BS), ("lease_liabilities", BS),
              ("cash_and_equivalents", BS), ("time_deposits", BS), ("undrawn_facilities", BS),
              ("interest_expense_borrowings", FY), ("finance_cost", FY), ("debt_principal_total", BS),
              ("sukuk_fixed_principal", BS), ("effective_interest_rate", FY), ("tau_eff", FY), ("da_total", FY),
              ("dividends_to_nci_fy25", FY), ("capex_guidance_2026", "FY26"), ("credit_rate_shock_bp", "")]
INPUT_ROWS += [("debt_maturity_principal", y) for y in MATURITY_YEARS]
INPUT_ROWS += [("credit_ebitda_multiplier", k) for k in MULTIPLIERS]
INPUT_ROWS += [("credit_threshold", k) for k in THRESHOLDS]

CAPEX_CELL = "B3"
CAPEX_LABEL = "User input: 2026 guidance shown, held flat is an assumption"
WF_ROWS = ["EBITDA", "Interest", "Tax", "Capex", "NCI dividends", "FCF", "Gross debt", "Net debt", "Leverage (x)"]


def _cell(ws, ref, value, color=BLACK, bold=False, fmt=None, fill=None):
    c = ws[ref]
    c.value = value
    c.font = Font(name=FONT, size=10, color=color, bold=bold)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


def _header(ws, row, labels):
    for j, label in enumerate(labels, 1):
        _cell(ws, f"{get_column_letter(j)}{row}", label, bold=True, fill=HEAD_FILL)


def _widths(ws, widths):
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w


def _inputs_sheet(wb, a):
    ws = wb.active
    ws.title = "Inputs"
    _cell(ws, "A1", "Inputs from inputs/assumptions.csv. Blue = sourced input or ANALYST setting. SAR m unless stated.",
          bold=True)
    _header(ws, 2, ["key", "value", "unit", "period", "source", "page"])
    refs = {}
    for i, (key, period) in enumerate(INPUT_ROWS, 3):
        r = a.row(key, period)
        assert "PLACEHOLDER" not in r.source, key
        _cell(ws, f"A{i}", key)
        _cell(ws, f"B{i}", float(r.value), color=BLUE, fmt="#,##0.00##")
        _cell(ws, f"C{i}", r.unit)
        _cell(ws, f"D{i}", period)
        _cell(ws, f"E{i}", r.source)
        _cell(ws, f"F{i}", r.page)
        refs[(key, period)] = f"Inputs!$B${i}"
    _widths(ws, [32, 13, 8, 11, 62, 34])
    return refs


def _metrics_sheet(wb, x):
    ws = wb.create_sheet("Metrics")
    _cell(ws, "A1", "FY25 credit metrics (SAR m). Live formulas on Inputs.", bold=True)
    _header(ws, 2, ["metric", "value", "unit", "definition"])
    e, debt = x[("group_ebitda", FY)], x[("total_borrowings", BS)]
    cash, td = x[("cash_and_equivalents", BS)], x[("time_deposits", BS)]
    low, high = x[("credit_threshold", "low")], x[("credit_threshold", "high")]
    principal = x[("debt_principal_total", BS)]
    rows = [
        ("net_debt", f"={debt}-{cash}-{td}", "SAR m", NUM,
         "Borrowings - cash - time deposits; leases excluded (company definition)"),
        ("net_debt_incl_leases", f"=B3+{x[('lease_liabilities', BS)]}", "SAR m", NUM, "Net debt + lease liabilities"),
        ("leverage", f"=B3/{e}", "x", TIMES, "Net debt / FY25 group EBITDA"),
        ("leverage_incl_leases", f"=B4/{e}", "x", TIMES, "Net debt incl. leases / FY25 group EBITDA"),
        ("ebitda_cushion_low", f"=1-B3/({low}*{e})", "ratio", PCT,
         "EBITDA fall that takes leverage to the low threshold"),
        ("ebitda_cushion_high", f"=1-B3/({high}*{e})", "ratio", PCT,
         "EBITDA fall that takes leverage to the high threshold"),
        ("interest_cover_borrowings", f"={e}/{x[('interest_expense_borrowings', FY)]}", "x", TIMES,
         "EBITDA / interest on borrowings"),
        ("interest_cover_finance_cost", f"={e}/{x[('finance_cost', FY)]}", "x", TIMES, "EBITDA / total finance cost"),
        ("liquidity", f"={cash}+{td}+{x[('undrawn_facilities', BS)]}", "SAR m", NUM,
         "Cash + time deposits + undrawn facilities"),
        ("floating_share", f"=1-{x[('sukuk_fixed_principal', BS)]}/{principal}", "ratio", PCT,
         "1 - fixed sukuk principal / total principal"),
        ("rate_shock_cost", f"=B12*{principal}*{x[('credit_rate_shock_bp', '')]}/{BP_PER_UNIT:.0f}", "SAR m", NUM,
         "Floating share x principal x rate shock"),
    ]
    for i, (name, formula, unit, fmt, note) in enumerate(rows, 3):
        _cell(ws, f"A{i}", name)
        _cell(ws, f"B{i}", formula, fmt=fmt)
        _cell(ws, f"C{i}", unit)
        _cell(ws, f"D{i}", note)
    _widths(ws, [30, 14, 8, 70])


def _waterfall_sheet(wb, x, inp):
    ws = wb.create_sheet("Waterfall")
    _cell(ws, "A1", "Annual waterfall from 31-Dec-25 (SAR m). Change only the yellow cell.", bold=True)
    _cell(ws, "A3", "Annual capex (SAR m)", bold=True)
    _cell(ws, CAPEX_CELL, inp["capex_guidance"], color=BLUE, fmt="#,##0.00", fill=YELLOW)
    _cell(ws, "C3", CAPEX_LABEL)
    _cell(ws, "A4", "EBITDA multiplier")
    _cell(ws, "B4", f"={x[('credit_ebitda_multiplier', 'flat')]}", color=GREEN, fmt="0.00")
    _cell(ws, "C4", "Flat scenario. Maturities refinanced; cash and time deposits constant; no EBITDA from new capacity.")
    _header(ws, 6, ["SAR m", "31-Dec-25"] + [str(y) for y in inp["years"]])
    row = {name: 7 + i for i, name in enumerate(WF_ROWS)}
    for name, i in row.items():
        _cell(ws, f"A{i}", name)
    liquid = f"{x[('cash_and_equivalents', BS)]}-{x[('time_deposits', BS)]}"
    _cell(ws, f"B{row['Gross debt']}", f"={x[('total_borrowings', BS)]}", color=GREEN, fmt=NUM)
    _cell(ws, f"B{row['Net debt']}", f"=B{row['Gross debt']}-{liquid}", fmt=NUM)
    for j in range(3, 3 + len(inp["years"])):
        c, p = get_column_letter(j), get_column_letter(j - 1)
        ref = {k: f"{c}{v}" for k, v in row.items()}
        _cell(ws, ref["EBITDA"], f"=$B$4*{x[('group_ebitda', FY)]}", fmt=NUM)
        _cell(ws, ref["Interest"], f"={x[('effective_interest_rate', FY)]}*{p}{row['Gross debt']}", fmt=NUM)
        _cell(ws, ref["Tax"], f"={x[('tau_eff', FY)]}*MAX({ref['EBITDA']}-{x[('da_total', FY)]}-{ref['Interest']},0)",
              fmt=NUM)
        _cell(ws, ref["Capex"], f"=${CAPEX_CELL[0]}${CAPEX_CELL[1:]}", fmt=NUM)
        _cell(ws, ref["NCI dividends"], f"={x[('dividends_to_nci_fy25', FY)]}", color=GREEN, fmt=NUM)
        _cell(ws, ref["FCF"], f"={ref['EBITDA']}-{ref['Interest']}-{ref['Tax']}-{ref['Capex']}-{ref['NCI dividends']}",
              fmt=NUM)
        _cell(ws, ref["Gross debt"], f"={p}{row['Gross debt']}-{ref['FCF']}", fmt=NUM)
        _cell(ws, ref["Net debt"], f"={ref['Gross debt']}-{liquid}", fmt=NUM)
        _cell(ws, ref["Leverage (x)"], f'=IF({ref["EBITDA"]}>0,{ref["Net debt"]}/{ref["EBITDA"]},"EBITDA<=0")',
              fmt=TIMES)
    _widths(ws, [24, 14] + [13] * len(inp["years"]))


def _breakeven_sheet(wb, table):
    ws = wb.create_sheet("Breakeven")
    _cell(ws, "A1", "Values from Python (src/credit.py bisection), not live formulas. SAR m per year.", bold=True)
    cols = [("Scenario", "scenario"), ("EBITDA multiplier", "multiplier"), ("Threshold (x)", "threshold"),
            ("Breakeven capex", "breakeven_capex"), ("First breach year", "first_breach_year"),
            ("Breakeven, +shock on floating share", "breakeven_capex_shock_floating"),
            ("Breakeven, +shock on all debt", "breakeven_capex_shock_all_debt")]
    _header(ws, 2, [c[0] for c in cols])
    for i, r in enumerate(table, 3):
        for j, (_, k) in enumerate(cols, 1):
            fmt = "#,##0" if "capex" in k else ("0.0" if k in ("multiplier", "threshold") else None)
            _cell(ws, f"{get_column_letter(j)}{i}", r[k], fmt=fmt)
    _widths(ws, [12, 17, 14, 16, 17, 34, 29])


def _maturities_sheet(wb, x):
    ws = wb.create_sheet("Maturities")
    _cell(ws, "A1", "Principal maturity profile at 31-Dec-25 (SAR m). Audited FS Note 35.10.", bold=True)
    _header(ws, 2, ["Year", "Principal", "Share of principal"])
    last = 2 + len(MATURITY_YEARS)
    for i, y in enumerate(MATURITY_YEARS, 3):
        _cell(ws, f"A{i}", y)
        _cell(ws, f"B{i}", f"={x[('debt_maturity_principal', y)]}", color=GREEN, fmt=NUM)
        _cell(ws, f"C{i}", f"=B{i}/{x[('debt_principal_total', BS)]}", fmt=PCT)
    _cell(ws, f"A{last + 1}", "Total", bold=True)
    _cell(ws, f"B{last + 1}", f"=SUM(B3:B{last})", bold=True, fmt=NUM)
    _cell(ws, f"C{last + 1}", f"=B{last + 1}/{x[('debt_principal_total', BS)]}", bold=True, fmt=PCT)
    _widths(ws, [10, 14, 18])


def build(path, inp, table):
    wb = Workbook()
    x = _inputs_sheet(wb, Assumptions())
    _metrics_sheet(wb, x)
    _waterfall_sheet(wb, x, inp)
    _breakeven_sheet(wb, table)
    _maturities_sheet(wb, x)
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)
