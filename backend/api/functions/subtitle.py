from .ai_client import transcribe_audio_file


class STTModel:
    def __init__(self, model='medium'):
        pass
    
    def load_model(self):
        pass
            

    def transcribe(self, audio_path):
        try:
            response = transcribe_audio_file(audio_path)
            
            timelines = []
            for idx, segment in enumerate(response.get('segments', [])):
                start = round(segment['start'], 3)
                end = round(segment['end'], 3)
                text = segment['text'].strip()
                timelines.append({'index': idx, 'start': start, 'end': end, 'subtitle': text})
            
            return timelines
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise e


if __name__ == "__main__":
    model = STTModel(model='base')
    print(model.transcribe('/Users/sungho/dev/AudiLex/backend/data/audio/1.wav'))
