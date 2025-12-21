from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import shutil
import os
from pathlib import Path
from faster_whisper import WhisperModel
import ollama

app = FastAPI()

UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

print("Loading Whisper Model...")
model = WhisperModel("large-v3", device="cuda", compute_type="int8")
print("Whisper Model Loaded!")

class TranscribeRequest(BaseModel):
    file_path: str
    language: str = None

@app.get("/")
def read_root():
    return {"status": "AI Server is running", "gpu": "RTX 3060 Ti Ready"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_path = UPLOAD_DIR / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        segments, info = model.transcribe(str(temp_path), beam_size=5)
        
        result = []
        for segment in segments:
            result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            
        return {"language": info.language, "segments": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass

class PronounceRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None

class TranslateRequest(BaseModel):
    text: str
    target_lang: Optional[str] = "ko"

@app.post("/translate")
def get_translation(req: TranslateRequest):
    system_prompt = (
        "You are a professional translator. Translate the following text into natural, fluent Korean. "
        "Consider the context and nuance. Output ONLY the translated text. Do not include any explanations or notes."
    )
    
    user_prompt = f"Translate the following text to Korean:\n\n{req.text}"

    try:
        response = ollama.chat(model='llama3:8b', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ])
        
        if not response or 'message' not in response or 'content' not in response['message']:
             raise ValueError("Invalid response from Ollama")

        return {"translation": response['message']['content'].strip()}
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pronounce")
def get_pronounce(req: PronounceRequest):
    system_prompt = (
        "You are a linguistics expert. Convert the following text into Korean Hangul pronunciation (Hangulization/Transliteration). "
        "If the text is English, write how it sounds in Korean. "
        "If the text is Japanese, write the pronunciation in Korean. "
        "Output ONLY the Korean pronunciation. Do not include original text or explanations."
    )
    
    user_prompt = f"Convert this text to Korean pronunciation:\n\n{req.text}"

    try:
        response = ollama.chat(model='llama3:8b', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ])
        
        if not response or 'message' not in response or 'content' not in response['message']:
             raise ValueError("Invalid response from Ollama")

        return {"pronounce": response['message']['content'].strip()}
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
