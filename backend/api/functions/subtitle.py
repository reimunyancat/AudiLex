import whisper
import json
import os


class STTmodel:
    def __init__(self, model='medium'):
        self.model_size=model
        self.model = None
    
    def load_model(self):
        self.model = whisper.load_model(self.model_size)
        print('model loaded')
            

    def transcribe(self, audio_path):
        # TODO: status에 처리 진행중 으로 변경
        if not self.model:
            self.load_model()
        
        result = self.model.transcribe(audio_path, word_timestamps=True)

        timelines = []
        for segment in result['segments']:
            start = round(segment['start'],3)
            end = round(segment['end'],3)
            text = segment['text'].strip()
            timelines.append({'start':start, 'end':end, 'text':text})
        
        return timelines


if __name__ == "__main__":
    model = STTmodel(model='base')
    print(model.transcribe('/Users/sungho/dev/AudiLex/backend/data/audio/1.wav'))
