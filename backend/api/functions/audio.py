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

def download_audio(youtube_link: str):
    """Download audio for a single YouTube link and return metadata."""
    data_root = _data_root()
    audio_dir = data_root / 'audio'
    audio_dir.mkdir(parents=True, exist_ok=True)

    video_id, title, final_mp3_path = _download_youtube_audio(youtube_link, audio_dir)
    return {
        'video_id': video_id,
        'title': title,
        'absolute_path': str(final_mp3_path),
        'relative_path': os.path.relpath(final_mp3_path, settings.BASE_DIR),
    }


def _download_raw_audio(youtube_link: str, output_dir: Path | None = None) -> Path:
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        _, title, final_path = _download_youtube_audio(youtube_link, output_dir)
        print(f"Downloaded '{title}' to {final_path}")
        return final_path

    metadata = download_audio(youtube_link)
    print(f"Downloaded '{metadata['title']}' to {metadata['absolute_path']}")
    return Path(metadata['absolute_path'])


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