# agents/scraping_agent/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI()

@app.get("/")                        
def health_check():
    return {"status": "ok"}

@app.get("/earnings")
def get_earnings(symbol: str):
    """
    Returns latest earnings or filings for the given ticker symbol.
    """
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Alpha Vantage API key required for earnings.")
    url = "https://www.alphavantage.co/query"
    params = {"function": "EARNINGS", "symbol": symbol, "apikey": api_key}
    response = requests.get(url, params=params)
    data = response.json()
    if not data or "annualEarnings" not in data:
        raise HTTPException(status_code=404, detail="No earnings data found.")
    return {"symbol": symbol, "earnings": data}
