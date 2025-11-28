import yt_dlp
import os
from urllib.parse import urlparse

def get_info(youtube_url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
    return info

def download_audio(youtube_url, download_path):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
    
    if 'entries' in info:
        playlist_title = info.get('title', 'playlist')
        playlist_path = os.path.join(download_path, playlist_title)
        if not os.path.exists(playlist_path):
            os.makedirs(playlist_path)
        outtmpl = os.path.join(playlist_path, '%(title)s.%(ext)s')
    else:
        outtmpl = os.path.join(download_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'writethumbnail': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(youtube_url, download=True)
    
    return youtube_url

def extract_video_ids(url):
    parsed_url = urlparse(url)
    
    if 'youtube.com' in parsed_url.netloc and 'playlist' in parsed_url.path:
        info = get_info(url)
        if 'entries' in info:
            return [entry['id'] for entry in info['entries']]
    elif 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
        return [url]
    
    return [url]

def process(url, download_path):
    video_urls = extract_video_ids(url)
    
    for video_url in video_urls:
        print(f"Downloading audio: {video_url}")
        download_audio(video_url, download_path)
    print(f"Completed: {video_url}")

def main():
    url = input('Enter the YouTube URL: ')
    
    download_path = 'downloads'
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    process(url, download_path)

if __name__ == '__main__':
    main()