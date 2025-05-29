# agents/voice_agent/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import pipeline
from TTS.api import TTS
import io
import soundfile as sf

app = FastAPI()
# Initialize Whisper ASR pipeline (choose model per resource constraints)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-small")

# Initialize Coqui TTS (LJSpeech model for English)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

class TextRequest(BaseModel):
    text: str

@app.get("/")                        
def health_check():
    return {"status": "ok"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio to text.
    """
    contents = await file.read()
    # Use Whisper pipeline
    result = asr(contents, chunk_length_s=30)  # Whisper can process up to 30s chunks
    text = result.get("text", "")
    return {"text": text}

@app.post("/speak")
def synthesize_speech(req: TextRequest):
    """
    Convert text to speech (returns WAV bytes).
    """
    audio_array = tts.tts(req.text)  # generate numpy array
    # Write to WAV in-memory
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, tts.synthesizer.output_sample_rate, format='WAV')
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/wav")
