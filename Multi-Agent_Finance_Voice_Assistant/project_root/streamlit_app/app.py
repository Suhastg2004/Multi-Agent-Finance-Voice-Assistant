# streamlit_app/app.py
import streamlit as st
import requests
import base64
import io

st.title("Financial Voice Assistant")
st.write("Ask a question about a stock by recording your voice:")

# Record audio from microphone (up to default timeout ~10s)
audio_input = st.audio_input("Record your question here")
if audio_input is not None:
    st.write("Processing your query...")
    # Convert UploadedFile to raw bytes
    raw_bytes = audio_input.read()
    # Prepare multipart form data
    files = {"file": ("query.wav", raw_bytes, "audio/wav")}
    # Call the orchestrator
    res = requests.post("http://localhost:8000/query", files=files)
    if res.status_code == 200:
        data = res.json()
        summary = data.get("summary", "")
        audio_b64 = data.get("audio", "")
        st.subheader("Summary:")
        st.write(summary)
        if audio_b64:
            # Decode base64 to bytes and play
            audio_bytes = base64.b64decode(audio_b64)
            st.audio(audio_bytes, format="audio/wav")
    else:
        st.error(f"Error: {res.status_code} - {res.text}")
