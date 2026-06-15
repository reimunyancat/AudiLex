from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import re
from pathlib import Path
from faster_whisper import WhisperModel
from openai import OpenAI

app = FastAPI()

UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

print("Loading Whisper Model...")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("Whisper Model Loaded!")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY"),
)
MODEL_NAME = "qwen/qwen3-next-80b-a3b-instruct"

def clean_output(text):
    if not text:
        return text
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    if len(text) >= 2 and text[0] in "\"'“「" and text[-1] in "\"'”」":
        text = text[1:-1].strip()
    return text


class TranscribeRequest(BaseModel):
    file_path: str
    language: str = None


@app.get("/")
def read_root():
    return {"status": "AI Server is running", "device": "cpu", "model": MODEL_NAME}


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_path = UPLOAD_DIR / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        segments, info = model.transcribe(
            str(temp_path),
            beam_size=5,
            vad_filter=False
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
        "당신은 영상 자막·노래 가사 전문 한국어 번역가입니다. 주어진 텍스트를 자연스럽고 매끄러운 한국어로 옮기세요.\n\n"
        "핵심 원칙:\n"
        "1. 직역하지 마세요. 단어를 하나하나 그대로 옮기지 말고, 한국 사람이 실제로 말하는 자연스러운 표현으로 옮기세요.\n"
        "2. 입력은 노래 가사나 짧은 자막 조각일 수 있습니다. 함축적이고 시적인 느낌을 살리되, 어색하거나 기계번역 같은 표현은 피하세요.\n"
        "3. 짧은 구어체·구어로 자연스럽게. 가사답게 간결하고 리듬감 있게 옮기세요.\n"
        "4. 번역된 한국어만 출력하세요. 원문, 설명, 주석, 괄호 메모, 따옴표, 이모지는 절대 넣지 마세요.\n"
        "5. 모든 단어를 번역하세요. 외국어 단어를 그대로 남기지 마세요 (고유명사 제외).\n"
        "6. 문장이 불완전하거나 이상해도 맥락상 가장 그럴듯한 자연스러운 한국어로 옮기세요."
    )

    user_prompt = f"다음 텍스트를 자연스러운 한국어로 번역:\n\n{req.text}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.35,
            top_p=0.9,
            max_tokens=1024,
        )

        content = response.choices[0].message.content if response.choices else None
        content = clean_output(content)
        if not content:
            raise ValueError("Invalid response from NIM")

        return {"translation": content}
    except Exception as e:
        print(f"NIM Error: {e}")
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
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )

        content = response.choices[0].message.content if response.choices else None
        content = clean_output(content)
        if not content:
            raise ValueError("Invalid response from NIM")

        return {"pronounce": content}
    except Exception as e:
        print(f"NIM Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
