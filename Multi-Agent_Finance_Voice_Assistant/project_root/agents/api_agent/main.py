# agents/api_agent/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import yfinance as yf

app = FastAPI()

class StockRequest(BaseModel):
    symbol: str
    
@app.get("/")                                
def health_check():
    return {"status": "ok"}

@app.get("/stock")
def get_stock(symbol: str):
    """
    Returns recent historical price data for the given ticker symbol.
    """
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if api_key:
        # Use Alpha Vantage Time Series API if key is available
        url = "https://www.alphavantage.co/query"
        params = {"function": "TIME_SERIES_DAILY_ADJUSTED",
                  "symbol": symbol,
                  "outputsize": "compact",
                  "apikey": api_key}
        response = requests.get(url, params=params)
        data = response.json()
        if "Error Message" in data or not data:
            raise HTTPException(status_code=404, detail="Symbol not found in Alpha Vantage.")
        return {"source": "AlphaVantage", "data": data}
    else:
        # Fallback to Yahoo Finance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo", interval="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail="Symbol not found via Yahoo Finance.")
        hist.reset_index(inplace=True)
        # Convert Timestamp to isoformat strings
        hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")
        records = hist.to_dict(orient="records")
        return {"source": "YahooFinance", "symbol": symbol, "history": records}
