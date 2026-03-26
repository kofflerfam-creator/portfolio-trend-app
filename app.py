import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(layout="wide")
st.title("📊 Portfolio Trend Analyzer")

TICKERS = [
    "WDC","MU","KTOS","RKLB","VRT",
    "GEV","GE","GOOGL","NVDA",
    "TSLA","SYK","AMZN","META","MSFT","V"
]

DATA_FILE = "prices.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.DataFrame(columns=["ticker","date","price"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()
today = datetime.today().date()

for ticker in TICKERS:
    hist = yf.Ticker(ticker).history(period="1d")
    if not hist.empty:
        close_price = round(float(hist["Close"].iloc[-1]), 2)
        df = df[~((df.ticker == ticker) & (df.date == str(today)))]
        df = pd.concat([
            df,
            pd.DataFrame([[ticker, today, close_price]],
                         columns=["ticker","date","price"])
        ])

save_data(df)

def pct(curr, past):
    if past is None or pd.isna(past) or past == 0:
        return None
    return round((curr - past) / past * 100, 2)

rows = []

for ticker in TICKERS:
    hist = df[df.ticker == ticker].sort_values("date")
    if hist.empty:
        continue

    current = hist.iloc[-1].price

    def ago(days):
        d = today - timedelta(days=days)
        past = hist[hist.date <= str(d)]
        return past.iloc[-1].price if not past.empty else None

    p3m = pct(current, ago(90))
    p6m = pct(current, ago(180))
    p1y = pct(current, ago(365))
    p2y = pct(current, ago(730))

    trend_vals = [v for v in [p3m, p6m, p1y, p2y] if v is not None]
    trend_score = round(sum(trend_vals) / len(trend_vals), 2) if trend_vals else None

    if p3m and p6m and p1y and p3m > 0 and p6m > 0 and p1y > 0:
        signal = "✅ Stay"
    elif p3m and p6m and p1y and p3m < 0 and p6m < 0 and p1y < 0:
        signal = "❌ Exit Risk"
    else:
        signal = "⚠️ Watch"

    rows.append({
        "Ticker": ticker,
        "% 3M": p3m,
        "% 6M": p6m,
        "% 1Y": p1y,
        "% 2Y": p2y,
        "Trend Score": trend_score,
        "Signal": signal
    })

result = pd.DataFrame(rows).sort_values("Trend Score", ascending=False)
st.dataframe(result, use_container_width=True)
``



