import os
from pathlib import Path
import yt_dlp
import requests
from models import Processing
from django.conf import settings

def _download_youtube_audio(youtube_link: str, output_dir: Path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_link, download=True)
        video_id = info.get('id')
        title = info.get('title', 'Unknown Title')
        final_mp3_path = output_dir / f"{video_id}.mp3"
        return video_id, title, final_mp3_path

def _save_audio_db(job: Processing, title: str, final_mp3_path: Path):
    filename_for_db = os.path.relpath(final_mp3_path, settings.DATA_ROOT)
    job.title = title
    job.audio_file_path = filename_for_db
    job.download_status = Processing.Status.SUCCESS
    job.save()

def download_audio(job_id):
    try:
        job = Processing.objects.get(pk=job_id)
        job.download_status = Processing.Status.PROCESSING
        job.save()

        audio_dir = settings.DATA_ROOT / 'audio'
        os.makedirs(audio_dir, exist_ok=True)

        video_id, title, final_mp3_path = _download_youtube_audio(job.youtube_link, audio_dir)
        _save_audio_db(job, title, final_mp3_path)

        print(f"Download complete. Sending to STT server for transcription: {job.id}...")
        
        transcript_dir = settings.DATA_ROOT / 'transcript'
        os.makedirs(transcript_dir, exist_ok=True)
        
        try:
            with open(final_mp3_path, 'rb') as audio_file:
                files = {'audio': (audio_file.name, audio_file, 'audio/mpeg')}
                stt_response = requests.post(
                    f"{settings.STT_SERVER_URL}/transcribe",
                    files=files,
                    timeout=3600
                )
            stt_response.raise_for_status()
            transcription_result = stt_response.json()

            job.transcript = transcription_result['text']
            job.transcript_status = Processing.Status.SUCCESS
            job.save()
            print(f"Transcription complete for {job.id}.")

        except requests.exceptions.RequestException as req_e:
            print(f"Error communicating with STT server for {job.id}: {req_e}")
            job.transcript_status = Processing.Status.FAILED
            job.save()
        except Exception as e:
            print(f"Error processing transcription result for {job.id}: {e}")
            job.transcript_status = Processing.Status.FAILED
            job.save()


    except Exception as e:
        print(f"Error processing {job_id}: {e}")
        job.download_status = Processing.Status.FAILED
        job.save()