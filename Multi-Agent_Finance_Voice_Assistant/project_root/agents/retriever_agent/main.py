# agents/retriever_agent/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
import pinecone
from sentence_transformers import SentenceTransformer

# Initialize Pinecone once
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"),
              environment=os.getenv("PINECONE_ENV"))
index_name = "financial-docs"
index = pinecone.Index(index_name)

app = FastAPI()
embedder = SentenceTransformer('all-MiniLM-L6-v2')

class QueryRequest(BaseModel):
    query: str

@app.get("/")                        
def health_check():
    return {"status": "ok"}

@app.post("/retrieve")
def retrieve_docs(req: QueryRequest):
    """
    Perform vector similarity search over cached documents.
    """
    vector = embedder.encode(req.query).tolist()
    res = index.query(vector=vector, top_k=5, include_metadata=True)
    docs = []
    for match in res['matches']:
        metadata = match['metadata']
        text = metadata.get("text", "")
        docs.append({"id": match['id'], "text": text[:200]})
    return {"documents": docs}
