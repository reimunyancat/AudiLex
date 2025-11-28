import whisper
import json
import os

DATA_PATH = 'backend/data'


class STTmodel:
    def __init__(self):
        self.model_size="medium"
        self.model
    
    def load_model(self):
        self.model = whisper.load_model(self.model_size)
        print('model loaded')
            

    def transcribe(self, id):
        # TODO: status에 처리 진행중 으로 변경
        if not self.model:
            self.load_model()
        
        audio_path = os.path.join(DATA_PATH, 'audio', id, '.mp3')

        result = self.model.transcribe(audio_path, word_timestamps=True)

        output_path = os.path.join(DATA_PATH, 'transcript', id)

        with open(f'{output_path}_verbose.json', 'w', encoding='utf-8') as f: # for test
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        with open(f'{output_path}.json', 'w', encoding='utf-8') as f: 
            timelines = []
            for segment in result['segments']:
                start = round(segment['start'],1)
                end = round(segment['end'],1)
                text = segment['text'].strip()
                timelines.append({'start':start, 'end':end, 'text':text})
            json.dump(timelines, f, ensure_ascii=False, indent=4)
        
        print('finished')