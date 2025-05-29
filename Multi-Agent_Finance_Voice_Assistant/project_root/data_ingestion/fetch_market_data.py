import yfinance as yf
import json

tickers = ["APPLE" , "MICROSOFT", "RELIANCE","GOOGLE"]
result = {}

for symbol in tickers:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period='6mo', interval='1d')
    hist.reset_index(inplace=True)
    #convert to record list
    result[symbol] = hist.to_dict(orient='records')
    
with open("market_data_cache.json", "w") as f:
    json.dump(result, f)
print("Market data fetched and saved.")
    