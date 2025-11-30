import os
import base64
import mimetypes
import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Audio
from .functions.audio import download_audio as process_audio_download
from .functions.subtitle import STTModel
from .functions.preprocess import PreprocessModel
from .functions.status import get_status_by_id, get_all_statuses


stt_model = STTModel()
preprocess_model = PreprocessModel()

# 오디오 데이터에서 데이터가 덮어씌워지는 거 방지
audio_data_locks = {}
audio_data_locks_lock = threading.Lock()

def get_audio_lock(audio_id):
    """Get or create a lock for a specific audio record."""
    with audio_data_locks_lock:
        if audio_id not in audio_data_locks:
            audio_data_locks[audio_id] = threading.Lock()
        return audio_data_locks[audio_id]


@api_view(['POST'])
def download_audio(request):
    """
    API endpoint to download audio from a YouTube video.
    """
    
    if request.method == 'POST':
        video_url = request.data.get('video_url')
        if not video_url:
            return Response({'error': 'video_url is required'}, status=drf_status.HTTP_400_BAD_REQUEST)

        audio = Audio.objects.create(
            youtube_link=video_url,
        )

        audio.audio_status = Audio.Status.PROCESSING
        audio.save(update_fields=['audio_status'])

        try:
            download_metadata = process_audio_download(video_url)
        except Exception as exc:
            audio.audio_status = Audio.Status.FAILED
            audio.save(update_fields=['audio_status'])
            return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

        audio.youtube_title = download_metadata['title']
        audio.audio_dir = download_metadata['relative_path']
        audio.audio_status = Audio.Status.FINISHED
        audio.save(update_fields=['youtube_title', 'audio_dir', 'audio_status'])

        response_data = {
            'message': 'Audio downloaded successfully.',
            'audio_id': str(audio.id),
            'status': audio.audio_status,
            'audio_dir': audio.audio_dir,
        }
        return Response(response_data, status=drf_status.HTTP_201_CREATED)

@api_view(['GET'])
def status(request, id):
    """
    받은 id의 transcribe, ipa, translate의 상황(진행 안됨, 진행중, 완료) 조회
    GET /api/status/{id}
    """
    data, error = get_status_by_id(id)
    if error:
        return Response({'error': error}, status=drf_status.HTTP_404_NOT_FOUND)
    return Response(data, status=drf_status.HTTP_200_OK)


@api_view(['GET'])
def statuses(request):
    """
    모든 transcribe, ipa, translate 상황 조회
    GET /api/statuses/
    """
    data = get_all_statuses()
    return Response(data, status=drf_status.HTTP_200_OK)

@api_view(['GET'])
def subtitle(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_path = audio.audio_dir
    if not audio_path:
        return Response({'error': 'audio_dir is not set for this audio record.'}, status=drf_status.HTTP_400_BAD_REQUEST)

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(settings.BASE_DIR, audio_path.lstrip('/'))

    if not os.path.exists(audio_path):
        return Response({'error': f'audio file not found at {audio_path}'}, status=drf_status.HTTP_404_NOT_FOUND)

    audio.subtitle_status = Audio.Status.PROCESSING
    audio.save(update_fields=['subtitle_status'])

    try:
        timelines = stt_model.transcribe(audio_path)
        formatted_timelines = [
            {
                'index': item.get('index'),
                'start': item.get('start'),
                'end': item.get('end'),
                'subtitle': item.get('subtitle') or item.get('text', ''),
            }
            for item in timelines
        ]

        audio_data = audio.audio_data or {}
        audio_data['data'] = formatted_timelines
        audio.audio_data = audio_data
        audio.subtitle_status = Audio.Status.FINISHED
        audio.save(update_fields=['audio_data', 'subtitle_status'])

        return Response({'subtitles': formatted_timelines}, status=drf_status.HTTP_200_OK)
    except Exception as exc:
        audio.subtitle_status = Audio.Status.FAILED
        audio.save(update_fields=['subtitle_status'])
        return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def translation(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_data = audio.audio_data or {}
    subtitles = audio_data.get('data') or []
    if not subtitles:
        return Response({'error': 'subtitles are not ready yet'}, status=drf_status.HTTP_400_BAD_REQUEST)

    audio.translation_status = Audio.Status.PROCESSING
    audio.save(update_fields=['translation_status'])

    # 번역과 발음이 동시에 요청될 때 audio_data가 덮어씌워지는 문제 방지
    lock = get_audio_lock(str(id))
    
    try:
        preprocess_model.load_model()
        translations = {}
        for i, entry in enumerate(subtitles):
            if entry.get('translate'):
                continue
            subtitle_text = entry.get('subtitle') or entry.get('text')
            if not subtitle_text:
                continue
            translation_text = preprocess_model.translate(subtitle_text)
            translations[i] = translation_text.strip()
    except Exception as exc:
        audio.translation_status = Audio.Status.FAILED
        audio.save(update_fields=['translation_status'])
        return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 번역과 발음이 동시에 요청될 때 audio_data가 덮어씌워지는 문제 방지
    with lock:
        # 가장 최신 audio_data를 가져오기 위해 다시 불러옴
        audio.refresh_from_db()
        audio_data = audio.audio_data or {}
        subtitles = audio_data.get('data') or []
        
        for i, translation_text in translations.items():
            if i < len(subtitles):
                subtitles[i]['translate'] = translation_text
        
        audio_data['data'] = subtitles
        audio.audio_data = audio_data
        audio.translation_status = Audio.Status.FINISHED
        audio.save(update_fields=['audio_data', 'translation_status'])

    return Response({'data': subtitles}, status=drf_status.HTTP_200_OK)

@api_view(['GET'])
def pronounce(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_data = audio.audio_data or {}
    subtitles = audio_data.get('data') or []
    if not subtitles:
        return Response({'error': 'subtitles are not ready yet'}, status=drf_status.HTTP_400_BAD_REQUEST)

    audio.pronounce_status = Audio.Status.PROCESSING
    audio.save(update_fields=['pronounce_status'])

    # 번역과 발음이 동시에 요청될 때 audio_data가 덮어씌워지는 문제 방지
    lock = get_audio_lock(str(id))
    
    try:
        preprocess_model.load_model()
        pronounces = {}
        for i, entry in enumerate(subtitles):
            if entry.get('pronounce'):
                continue
            subtitle_text = entry.get('subtitle') or entry.get('text')
            if not subtitle_text:
                continue
            pronounce_text = preprocess_model.pronounce(subtitle_text)
            pronounces[i] = pronounce_text.strip()
    except Exception as exc:
        audio.pronounce_status = Audio.Status.FAILED
        audio.save(update_fields=['pronounce_status'])
        return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 번역과 발음이 동시에 요청될 때 audio_data가 덮어씌워지는 문제 방지
    with lock:
        # 가장 최신 audio_data를 가져오기 위해 다시 불러옴
        audio.refresh_from_db()
        audio_data = audio.audio_data or {}
        subtitles = audio_data.get('data') or []
        
        for i, pronounce_text in pronounces.items():
            if i < len(subtitles):
                subtitles[i]['pronounce'] = pronounce_text
        
        audio_data['data'] = subtitles
        audio.audio_data = audio_data
        audio.pronounce_status = Audio.Status.FINISHED
        audio.save(update_fields=['audio_data', 'pronounce_status'])

    return Response({'data': subtitles}, status=drf_status.HTTP_200_OK)

@api_view(['GET'])
def audio_data(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_path = audio.audio_dir
    if not audio_path:
        return Response({'error': 'audio_dir is not set for this record.'}, status=drf_status.HTTP_400_BAD_REQUEST)

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(settings.BASE_DIR, audio_path.lstrip('/'))

    if not os.path.exists(audio_path):
        return Response({'error': f'audio file not found at {audio_path}'}, status=drf_status.HTTP_404_NOT_FOUND)

    try:
        with open(audio_path, 'rb') as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')
    except OSError as exc:
        return Response({'error': f'failed to read audio file: {exc}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    content_type, _ = mimetypes.guess_type(audio_path)
    if not content_type:
        content_type = 'application/octet-stream'

    return Response(
        {
            'audio_file': {
                'name': os.path.basename(audio_path),
                'content_type': content_type,
                'data': encoded_audio,
            },
            'audio_data': audio.audio_data or {},
        },
        status=drf_status.HTTP_200_OK,
    )

@api_view(['DELETE'])
def delete_audio(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_path = audio.audio_dir
    if audio_path and not os.path.isabs(audio_path):
        audio_path = os.path.join(settings.BASE_DIR, audio_path.lstrip('/'))

    try:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except OSError as exc:
        return Response({'error': f'failed to delete audio file: {exc}'}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    audio.delete()

    return Response({'message': 'Audio record and file deleted successfully.'}, status=drf_status.HTTP_200_OK)