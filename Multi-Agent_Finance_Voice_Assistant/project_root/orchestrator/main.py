# orchestrator/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import requests, base64, os
from langgraph.graph import StateGraph, END

app = FastAPI()

# Define the shared state schema
from typing import TypedDict
class State(TypedDict):
    input_text: str
    ticker: str
    market_data: dict
    earnings_data: dict
    documents: list
    metrics: dict
    summary: str
    audio: str  # will hold base64 audio

# Initialize the state graph
graph = StateGraph(State)

# Define node functions (each calls the respective agent)
def api_agent_node(state):
    sym = state["ticker"] or state["input_text"]
    resp = requests.get(f"http://localhost:8001/stock", params={"symbol": sym})
    state["market_data"] = resp.json() if resp.ok else {}
    return {"market_data": state["market_data"]}

def scraping_agent_node(state):
    sym = state["ticker"] or state["input_text"]
    resp = requests.get(f"http://localhost:8002/earnings", params={"symbol": sym})
    state["earnings_data"] = resp.json() if resp.ok else {}
    return {"earnings_data": state["earnings_data"]}

def retriever_agent_node(state):
    query = state["input_text"]
    resp = requests.post("http://localhost:8003/retrieve", json={"query": query})
    state["documents"] = resp.json().get("documents", []) if resp.ok else []
    return {"documents": state["documents"]}

def analysis_agent_node(state):
    data = {
        "market_data": state["market_data"].get("history", []),
        "earnings_data": state["earnings_data"],
        "documents": state["documents"]
    }
    resp = requests.post("http://localhost:8004/analyze", json=data)
    state["metrics"] = resp.json() if resp.ok else {}
    return {"metrics": state["metrics"]}

def language_agent_node(state):
    payload = {
        "symbol": state["ticker"],
        "market_data": state["market_data"].get("history", []),
        "earnings_data": state["earnings_data"],
        "metrics": state["metrics"]
    }
    resp = requests.post("http://localhost:8005/summarize", json=payload)
    state["summary"] = resp.json().get("summary", "") if resp.ok else ""
    return {"summary": state["summary"]}

def voice_agent_node(state):
    text = state["summary"]
    resp = requests.post("http://localhost:8006/speak", json={"text": text})
    if resp.ok:
        # Encode audio bytes to base64 for JSON transport
        state["audio"] = base64.b64encode(resp.content).decode()
    else:
        state["audio"] = ""
    return {"audio": state["audio"]}

# Add nodes to graph
graph.add_node("api_agent", api_agent_node)
graph.add_node("scraping_agent", scraping_agent_node)
graph.add_node("retriever_agent", retriever_agent_node)
graph.add_node("analysis_agent", analysis_agent_node)
graph.add_node("language_agent", language_agent_node)
graph.add_node("voice_agent", voice_agent_node)

# Connect the nodes in sequence
graph.set_entry_point("api_agent")
graph.add_edge("api_agent", "scraping_agent")
graph.add_edge("scraping_agent", "retriever_agent")
graph.add_edge("retriever_agent", "analysis_agent")
graph.add_edge("analysis_agent", "language_agent")
graph.add_edge("language_agent", "voice_agent")
graph.add_edge("voice_agent", END)

# Compile the graph
app_graph = graph.compile()

@app.post("/query")
async def handle_query(
    text: str = Form(None), 
    file: UploadFile = File(None)
):
    """
    Main endpoint for processing a query. Accepts either text or an audio file.
    Returns {"summary": ..., "audio": ...} where audio is base64.
    """
    # Determine input text: either directly or via Whisper
    if file:
        contents = await file.read()
        trans_resp = requests.post("http://localhost:8006/transcribe", files={"file": contents})
        if not trans_resp.ok:
            raise HTTPException(status_code=500, detail="STT failed.")
        query_text = trans_resp.json().get("text", "")
    elif text:
        query_text = text
    else:
        raise HTTPException(status_code=400, detail="No input provided.")
    # Initialize state
    state: State = {
        "input_text": query_text,
        "ticker": query_text.strip(),  # simplify: assume query_text is ticker
        "market_data": {},
        "earnings_data": {},
        "documents": [],
        "metrics": {},
        "summary": "",
        "audio": ""
    }
    # Run the graph
    final_state = app_graph.invoke(state)
    return {"summary": final_state["summary"], "audio": final_state["audio"]}
