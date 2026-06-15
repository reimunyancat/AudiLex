import os
from openai import OpenAI

class PreprocessModel:
    def __init__(self, model_name="qwen/qwen3-235b-a22b-instruct-2507"):
        self.model_name = model_name
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ.get("NVIDIA_API_KEY"),
        )
        
    def load_model(self):
        # NIM은 호스팅된 엔드포인트라 로컬로 받아둘 모델이 없어요. (ollama.pull 불필요)
        pass
    
    def translate(self, text):
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': '질문 주어진 응답만 하세요.'},
                {'role': 'user', 'content': f'{text} 이 문장을 한국어로 번역하시오'},
            ],
            temperature=0.6,
            max_tokens=256,
        )
        return resp.choices[0].message.content
        
    def pronounce(self, text):
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': '질문 주어진 응답만 하세요.'},
                {'role': 'user', 'content': f'{text} 이 문장을 후리가나로 표현하시오'},
            ],
            temperature=0.6,
            max_tokens=256,
        )
        return resp.choices[0].message.content
