# agents/language_agent/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()
# You can choose a model here (e.g., "google/flan-t5-large" or another open-source model).
summarizer = pipeline("summarization", model="google/flan-t5-large")

class SummarizeRequest(BaseModel):
    symbol: str
    market_data: list
    earnings_data: dict
    metrics: dict

@app.post("/summarize")
def summarize(req: SummarizeRequest):
    """
    Generate a summary given market data and analysis.
    """
    prompt = (f"Ticker: {req.symbol}\n"
              f"Recent Prices: {len(req.market_data)} days of data.\n"
              f"Earnings Report: {req.earnings_data.get('symbol', '')}\n"
              f"Metrics: Volatility {req.metrics.get('volatility'):.2f}, "
              f"Beta {req.metrics.get('beta')}\n"
              "Provide a concise financial summary and commentary.")
    summary = summarizer(prompt, max_length=150, clean_up_tokenization_spaces=True)[0]['summary_text']
    return {"summary": summary.strip()}
