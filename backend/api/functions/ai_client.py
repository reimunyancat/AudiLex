import requests
from django.conf import settings

AI_SERVER_URL = getattr(settings, 'AI_SERVER_URL', 'http://localhost:8000')

def transcribe_audio_file(file_path: str, language: str = None):
    url = f"{AI_SERVER_URL}/transcribe"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if language:
                data['language'] = language
            
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error communicating with AI server: {e}")
        raise e

def get_pronunciation(text: str, source_lang: str = None):
    url = f"{AI_SERVER_URL}/pronounce"
    
    payload = {
        "text": text,
        "source_lang": source_lang
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('pronounce')
    except Exception as e:
        print(f"Error communicating with AI server: {e}")
        raise e

def get_translation(text: str):
    url = f"{AI_SERVER_URL}/translate"
    
    payload = {
        "text": text,
        "target_lang": "ko"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('translation')
    except Exception as e:
        print(f"Error communicating with AI server: {e}")
        raise e
