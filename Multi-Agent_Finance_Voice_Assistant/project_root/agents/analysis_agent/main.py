# agents/analysis_agent/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np

app = FastAPI()

class AnalyzeRequest(BaseModel):
    market_data: list   # list of {"Date": "...", "Close": ...}
    earnings_data: dict
    documents: list

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Compute risk metrics (e.g. volatility, beta) from market_data.
    """
    # Create DataFrame of closing prices
    df = pd.DataFrame(req.market_data)
    if df.empty or "Close" not in df:
        return {"volatility": None, "beta": None}
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)
    df.set_index('Date', inplace=True)
    returns = df['Close'].pct_change().dropna()
    if returns.empty:
        return {"volatility": None, "beta": None}
    # Annualized volatility (assuming ~252 trading days)
    vol = float(returns.std() * np.sqrt(252))
    # For beta, compare to S&P 500 (^GSPC)
    try:
        import yfinance as yf
        sp = yf.Ticker("^GSPC").history(period="1mo", interval="1d")
        sp_returns = sp['Close'].pct_change().dropna()
        # Align on dates
        combined = pd.concat([returns, sp_returns], axis=1, join='inner').dropna()
        beta = float(np.cov(combined.iloc[:,0], combined.iloc[:,1])[0,1] 
                     / np.var(combined.iloc[:,1]))
    except Exception:
        beta = None
    return {"volatility": vol, "beta": beta}
