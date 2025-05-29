# data_ingestion/upload_to_pinecone.py
import pinecone
from sentence_transformers import SentenceTransformer
from constants import PINECONE_API_KEY, PINECONE_ENV
import json

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index("financial-docs")

model = SentenceTransformer('all-MiniLM-L6-v2')
with open("earnings_data_cache.json") as f:
    earnings = json.load(f)

for doc_id, entry in enumerate(earnings.get("AAPL", [])):
    text = entry.get("transcript", "")
    if not text: 
        continue
    vector = model.encode(text).tolist()
    metadata = {"ticker": "AAPL", "text": text}
    index.upsert([(str(doc_id), vector, metadata)])
print("Earnings transcripts indexed in Pinecone.")
