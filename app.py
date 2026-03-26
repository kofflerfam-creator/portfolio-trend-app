import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(layout="wide")
st.title("📊 Portfolio Trend Analyzer")

TICKERS = [
    "WDC", "MU", "KTOS", "RKLB", "VRT",
    "GEV", "GE", "GOOGL", "NVDA",
    "TSLA", "SYK", "AMZN", "META", "MSFT", "V"
]

DATA_FILE = "prices.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.DataFrame(columns=["ticker", "date", "price"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()
today = datetime.today().date()

for ticker in TICKERS:
    data = yf.Ticker(ticker).history(period="1d")
    if not data.empty:
        price = round(float(data["Close"].iloc[-1]), 2)
        df = df[~((df.ticker == ticker) & (df.date == str(today)))]
        df = pd.concat(
            [df, pd.DataFrame([[ticker, today, price]], columns=["ticker", "date", "price"])]
        )

save_data(df)

def pct_change(current, past):
    if pd.isna(past) or past == 0:
        return None
    return round((current - past) / past * 100, 2)

rows = []

for ticker in TICKERS:
    hist = df[df.ticker == ticker].sort_values("date")
    if hist.empty:
        continue

    current = hist.iloc[-1].price

    def price_days_ago(days):
        target = today - timedelta(days=days)
        past = hist[hist.date <= str(target)]
        return past.iloc[-1].price if not past.empty else None

    p3m = pct_change(current, price_days_ago(90))
    p6m = pct_change(current, price_days_ago(180))
    p1y = pct_change(current, price_days_ago(365))
    p2y = pct_change(current, price_days_ago(730))

    trend_score = pd.Series([p3m, p6m, p1y, p2y]).mean()

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
        "Trend Score": round(trend_score, 2) if not pd.isna(trend_score) else None,
        "Signal": signal
    })

result = pd.DataFrame(rows).sort_values("Trend Score", ascending=False)
st.dataframe(result, use_container_width=True)
``
