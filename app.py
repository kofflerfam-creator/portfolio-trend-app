import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Font, Border, Side, PatternFill

# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------
st.set_page_config(layout="wide")
st.title("Portfolio Trend Analyzer")

# -------------------------------------------------
# PORTFOLIOS
# -------------------------------------------------
PORTFOLIOS = {
    "Portfolio 1 - Core": [
        "GOOGL", "SYK", "NVDA", "META",
        "AMZN", "V", "TSLA", "MSFT"
    ],
    "Portfolio 2 - Growth": [
        "VRT", "WDC", "MU",
        "GEV", "KTOS", "GE", "RKLB"
    ],
    "Portfolio 3 - Speculative": [
        "STX", "FIX", "PWR", "CAT",
        "RBC", "APH", "ONDS", "NRG",
        "PLTR", "CRDO", "AVAV", "HOOD"
    ]
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def pct_change(current, past):
    if past is None or past == 0:
        return None
    return (current - past) / past * 100

def trend_score(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None

# -------------------------------------------------
# MAIN CALCULATION
# -------------------------------------------------
today = date.today()
rows = []

for portfolio, tickers in PORTFOLIOS.items():
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(period="3y")
        if hist.empty:
            continue

        current_price = hist["Close"].iloc[-1]

        def price_since(d):
            h = hist[hist.index.date >= d]
            return h["Close"].iloc[0] if not h.empty else None

        start_month = today.replace(day=1)
        start_year = today.replace(month=1, day=1)

        mtd = pct_change(current_price, price_since(start_month))
        ytd = pct_change(current_price, price_since(start_year))
        p3m = pct_change(current_price, price_since(today - timedelta(days=90)))
        p6m = pct_change(current_price, price_since(today - timedelta(days=180)))
        p1y = pct_change(current_price, price_since(today - timedelta(days=365)))
        p2y = pct_change(current_price, price_since(today - timedelta(days=730)))

        score = trend_score([p3m, p6m, p1y, p2y])

        if p3m and p6m and p1y and p3m > 0 and p6m > 0 and p1y > 0:
            signal = "Stay"
        elif p3m and p6m and p1y and p3m < 0 and p6m < 0 and p1y < 0:
            signal = "Exit Risk"
        else:
            signal = "Watch"

        rows.append({
            "Portfolio": portfolio,
            "Ticker": ticker,
            "Current Price": current_price,
            "MTD %": mtd,
            "YTD %": ytd,
            "3M %": p3m,
            "6M %": p6m,
            "1Y %": p1y,
            "2Y %": p2y,
            "Trend Score": score,
            "Signal": signal
        })

# -------------------------------------------------
# FINAL DATAFRAME (NO DECIMALS)
# -------------------------------------------------
df = (
    pd.DataFrame(rows)
    .sort_values(["Portfolio", "Trend Score"], ascending=[True, False])
    .round(0)
)

# Convert floats to integers (clean look, blanks preserved)
df = df.astype(
    {c: "Int64" for c in df.columns if df[c].dtype == "float64"}
)

st.subheader("Download")
# (button is added later, after Excel formatting)

st.subheader("Portfolio Table")
st.dataframe(df, use_container_width=True)

# -------------------------------------------------
# EXCEL EXPORT WITH FORMATTING
# -------------------------------------------------
buffer = BytesIO()
df.to_excel(buffer, index=False)
buffer.seek(0)

wb = load_workbook(buffer)
ws = wb.active

# Fonts and borders
header_font = Font(name="Calibri", bold=True)
cell_font = Font(name="Calibri")

border = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin")
)

# Fills
fill_negative = PatternFill("solid", fgColor="F4C7C3")  # Red for negatives
fill_stay = PatternFill("solid", fgColor="C6EFCE")      # Green
fill_watch = PatternFill("solid", fgColor="FFEB9C")     # Yellow
fill_exit = PatternFill("solid", fgColor="F4C7C3")      # Red

# Identify Signal column
signal_col = None
for i, cell in enumerate(ws[1], start=1):
    if cell.value == "Signal":
        signal_col = i

# Apply styles
for r, row in enumerate(ws.iter_rows(), start=1):
    for c, cell in enumerate(row, start=1):
        cell.font = header_font if r == 1 else cell_font
        cell.border = border

        # Shade negative numeric values
        if r > 1 and isinstance(cell.value, (int, float)) and cell.value < 0:
            cell.fill = fill_negative

    # Signal coloring
    if r > 1 and signal_col:
        sig = ws.cell(row=r, column=signal_col)
        if sig.value == "Stay":
            sig.fill = fill_stay
        elif sig.value == "Watch":
            sig.fill = fill_watch
        elif sig.value == "Exit Risk":
            sig.fill = fill_exit

# Freeze header row
ws.freeze_panes = "A2"

# Auto column widths
for col in ws.columns:
    max_len = max(len(str(c.value)) if c.value else 0 for c in col)
    ws.column_dimensions[col[0].column_letter].width = max_len + 2

final_buffer = BytesIO()
wb.save(final_buffer)
final_buffer.seek(0)

st.download_button(
    label="Download report as Excel",
    data=final_buffer,
    file_name="portfolio_trend_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
