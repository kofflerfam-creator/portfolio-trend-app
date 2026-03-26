import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

st.set_page_config(layout="wide")
st.title("Portfolio Trend Analyzer")

# ---- Portfolio definitions ----
PORTFOLIOS = {
    "Portfolio 1 - Core": [
        "GOOGL", "SYK", "NVDA", "META", "AMZN", "V", "TSLA", "MSFT"
    ],
    "Portfolio 2 - Growth": [
        "VRT", "WDC", "MU", "GEV", "KTOS", "GE", "RKLB"
    ],
    "Portfolio 3 - Speculative": [
        "STX", "FIX", "PWR", "CAT", "RBC", "APH",
        "ONDS", "NRG", "PLTR", "CRDO", "AVAV", "HOOD"
    ]
}

ALL_TICKERS = [(p, t) for p, tickers in PORTFOLIOS.items() for t in tickers]

# ---- Helper functions ----
def pct_change(current, past):
    if past is None or past == 0:
        return None
    return round((current - past) / past * 100, 2)

def trend_score(values):
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None

# ---- Main calculation ----
today = date.today()
rows = []

for portfolio, ticker in ALL_TICKERS:
    hist = yf.Ticker(ticker).history(period="3y")
    if hist.empty:
        continue

    current_price = round(float(hist["Close"].iloc[-1]), 2)

    def ago(days):
        cutoff = today - timedelta(days=days)
        past = hist[hist.index.date <= cutoff]
        return float(past["Close"].iloc[-1]) if not past.empty else None

    p3m = pct_change(current_price, ago(90))
    p6m = pct_change(current_price, ago(180))
    p1y = pct_change(current_price, ago(365))
    p2y = pct_change(current_price, ago(730))

    score = trend_score([p3m, p6m, p1y, p2y])

    # Signal logic
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
        "3M %": p3m,
        "6M %": p6m,
        "1Y %": p1y,
        "2Y %": p2y,
        "Trend Score": score,
        "Signal": signal
    })

df = pd.DataFrame(rows).sort_values(
    by=["Portfolio", "Trend Score"],
    ascending=[True, False]
)

st.dataframe(df, use_container_width=True)

# ---- Excel download ----
st.download_button(
    label="Download report as Excel",
    data=df.to_excel(index=False, engine="openpyxl"),
    file_name="portfolio_trend_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
``
