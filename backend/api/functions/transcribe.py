import whisper
import json

DATA_PATH = 'backend/data'

class STTmodel:
    def __init__(self):
        self.model_size="medium"
        self.model = None
    
    def load_model(self):
        self.model = whisper.load_model(self.model_size)
        print('model loaded')
            

    def transcribe(self, audio_path, output_path_prefix):
        # TODO: status에 처리 진행중 으로 변경
        if not self.model:
            self.load_model()
        
        result = self.model.transcribe(audio_path, word_timestamps=True)

        with open(f'{output_path_prefix}_verbose.json', 'w', encoding='utf-8') as f: # for test
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        with open(f'{output_path_prefix}.json', 'w', encoding='utf-8') as f: 
            timelines = []
            for segment in result['segments']:
                start = round(segment['start'],1)
                end = round(segment['end'],1)
                text = segment['text'].strip()
                timelines.append({'start':start, 'end':end, 'text':text})
            json.dump(timelines, f, ensure_ascii=False, indent=4)
        
        print('finished')
