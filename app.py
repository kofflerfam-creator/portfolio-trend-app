import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

st.set_page_config(layout="wide")
st.title("Portfolio Trend Analyzer")

TICKERS = [
    "WDC", "MU", "KTOS", "RKLB", "VRT",
    "GEV", "GE", "GOOGL", "NVDA",
    "TSLA", "SYK", "AMZN", "META", "MSFT", "V"
]

def pct_change(current, past):
    if past is None or past == 0:
        return None
    return round((current - past) / past * 100, 2)

rows = []
today = date.today()

for ticker in TICKERS:
    hist = yf.Ticker(ticker).history(period="3y")

    if hist.empty:
        continue

    current = hist["Close"].iloc[-1]

    def ago(days):
        cutoff = today - timedelta(days=days)
        past = hist[hist.index.date <= cutoff]
        return past["Close"].iloc[-1] if not past.empty else None

    p3m = pct_change(current, ago(90))
    p6m = pct_change(current, ago(180))
    p1y = pct_change(current, ago(365))
    p2y = pct_change(current, ago(730))

    if p3m and p6m and p1y and p3m > 0 and p6m > 0 and p1y > 0:
        signal = "Stay"
    elif p3m and p6m and p1y and p3m < 0 and p6m < 0 and p1y < 0:
        signal = "Exit Risk"
    else:
        signal = "Watch"

    rows.append({
        "Ticker": ticker,
        "3M %": p3m,
        "6M %": p6m,
        "1Y %": p1y,
        "2Y %": p2y,
        "Signal": signal
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)
