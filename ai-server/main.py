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

MODEL_NAME = "llama3.1"
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
        segments, info = model.transcribe(
            str(temp_path), 
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300)
        )
        
        result = []
        for segment in segments:
            result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        return {"language": info.language, "segments": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Transcribe Error: {e}")
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
        "Rules:\n"
        "1. Output ONLY the translated Korean text.\n"
        "2. Do NOT include the original text.\n"
        "3. Do NOT add any explanations, notes, or parentheses like '(Note: ...)'.\n"
        "4. Do NOT add quotes around the translation.\n"
        "5. Translate accurately and naturally.\n"
        "6. If the text is incomplete or nonsensical, translate it as best as possible based on context.\n"
        "7. Do NOT use emojis or emoticons."
    )
    
    user_prompt = f"Translate this text to Korean:\n\n{req.text}"

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ], options={
            'temperature': 0.1,
            'num_ctx': 1024
        })
        
        if not response or 'message' not in response or 'content' not in response['message']:
             raise ValueError("Invalid response from Ollama")

        return {"translation": response['message']['content'].strip()}
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pronounce")
def get_pronounce(req: PronounceRequest):
    system_prompt = (
        "You are a strict transliteration machine. Your ONLY job is to convert the sound of the input text into Korean Hangul characters."
        "\n\n"
        "STRICT RULES:\n"
        "1. Output ONLY the Hangul pronunciation. NO other text.\n"
        "2. NEVER translate the meaning. (e.g., 'Apple' -> '애플' (O), '사과' (X))\n"
        "3. NEVER output consonants alone like 'ㄴㅇㄱㄷㅁㅇ'. Always form complete Hangul blocks.\n"
        "4. If the input is Russian, write how it sounds in Korean. (e.g., 'Да' -> '다')\n"
        "5. If the input is English, write how it sounds in Korean. (e.g., 'Love' -> '러브')\n"
        "6. Do NOT include the original text in the output.\n"
        "7. Do NOT add any notes, explanations, or punctuation."
    )
    
    user_prompt = f"Transliterate the sound of this text into Korean Hangul:\n\n{req.text}"

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ], options={
            'temperature': 0.0,
            'num_ctx': 1024
        })
        
        if not response or 'message' not in response or 'content' not in response['message']:
             raise ValueError("Invalid response from Ollama")

        return {"pronounce": response['message']['content'].strip()}
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
