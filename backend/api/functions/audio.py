import os
import argparse
from pathlib import Path
import yt_dlp

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.conf import settings

if not settings.configured:
    django.setup()

from ..models import Audio

def _data_root() -> Path:
    base_dir = Path(getattr(settings, "DATA_ROOT", Path(settings.BASE_DIR) / "data"))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


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

def _save_audio_db(job: Audio, title: str, final_mp3_path: Path):
    relative_path = os.path.relpath(final_mp3_path, settings.BASE_DIR)
    job.youtube_title = title
    job.audio_name = title
    job.audio_dir = relative_path
    job.audio_status = Audio.Status.FINISHED
    job.save(update_fields=[
        'youtube_title',
        'audio_name',
        'audio_dir',
        'audio_status',
    ])

def download_audio(job_id):
    job = None
    try:
        job = Audio.objects.get(pk=job_id)
        job.audio_status = Audio.Status.PROCESSING
        job.save(update_fields=['audio_status'])

        data_root = _data_root()
        audio_dir = data_root / 'audio'
        audio_dir.mkdir(parents=True, exist_ok=True)

        _, title, final_mp3_path = _download_youtube_audio(job.youtube_link, audio_dir)
        _save_audio_db(job, title, final_mp3_path)

    except Audio.DoesNotExist:
        print(f"Audio job {job_id} does not exist")
    except Exception as e:
        print(f"Error processing {job_id}: {e}")
        if job:
            job.audio_status = Audio.Status.FAILED
            job.save(update_fields=['audio_status'])


def _download_raw_audio(youtube_link: str, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or (_data_root() / 'audio')
    output_dir.mkdir(parents=True, exist_ok=True)
    _, title, final_path = _download_youtube_audio(youtube_link, output_dir)
    print(f"Downloaded '{title}' to {final_path}")
    return final_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone audio download tester")
    parser.add_argument("youtube_link", help="YouTube URL to download")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to store the downloaded audio (defaults to data/audio)",
    )
    args = parser.parse_args()

    output_path = _download_raw_audio(
        args.youtube_link,
        Path(args.output_dir) if args.output_dir else None,
    )
    print(f"Audio saved at: {output_path}")