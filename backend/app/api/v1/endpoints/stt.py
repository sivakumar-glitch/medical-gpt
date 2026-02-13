from fastapi import APIRouter, UploadFile, File, HTTPException
import whisper
import tempfile
import os
from langsmith import traceable

router = APIRouter()

# Load Whisper model (downloads on first use)
model = None

def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model("base")  # Use "base" for speed, can change to "small", "medium", etc.
    return model

@router.post("/transcribe")
@traceable(name="Whisper STT")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm')):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use WAV, MP3, M4A, FLAC, OGG, or WEBM.")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Transcribe
        whisper_model = get_whisper_model()
        result = whisper_model.transcribe(temp_path)
        transcription = result["text"].strip()
        return {"transcription": transcription}
    finally:
        # Clean up temp file
        os.unlink(temp_path)