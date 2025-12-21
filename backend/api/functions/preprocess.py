import ollama

class PreprocessModel:
    def __init__(self, model_name='gemma3:4b'):
        self.model_name = model_name

    def load_model(self):
        if self.model_name not in ollama.list():
            print("downloading model")
            ollama.pull(self.model_name)

    def translate(self, text):
        resp = ollama.chat(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': '질문 주어진 응답만 하세요.'},
                {'role': 'user', 'content': f'{text} 이 문장을 한국어로 번역하시오'},
            ],
            options={
                'temperature': 0.6,
                'num_predict': 256,
            },
        )
        return resp['message']['content']

    def pronounce(self, text):
        resp = ollama.chat(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': '질문 주어진 응답만 하세요.'},
                {'role': 'user', 'content': f'{text} 이 문장을 후리가나로 표현하시오'},
            ],
            options={
                'temperature': 0.6,
                'num_predict': 256,
            },
        )
        return resp['message']['content']
