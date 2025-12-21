import os
import base64
import mimetypes
import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Audio
from .functions.audio import download_audio as process_audio_download
from .functions.subtitle import STTModel
from .functions.status import get_status_by_id, get_all_statuses
from .functions.ai_client import get_pronunciation, get_translation
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


stt_model = STTModel()

audio_data_locks = {}
audio_data_locks_lock = threading.Lock()

def get_audio_lock(audio_id):
    with audio_data_locks_lock:
        if audio_id not in audio_data_locks:
            audio_data_locks[audio_id] = threading.Lock()
        return audio_data_locks[audio_id]


def send_ws_update(audio_id, message_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'audio_{audio_id}',
        {
            'type': 'audio_update',
            'message': {
                'type': message_type,
                'data': data
            }
        }
    )


@api_view(['POST'])
def download_audio(request):
    if request.method == 'POST':
        video_url = request.data.get('video_url')
        uploaded_file = request.FILES.get('file')

        if not video_url and not uploaded_file:
            return Response({'error': 'video_url or file is required'}, status=drf_status.HTTP_400_BAD_REQUEST)

        if uploaded_file:
            audio = Audio.objects.create(
                youtube_title=uploaded_file.name,
                source_file=uploaded_file,
                audio_status=Audio.Status.FINISHED
            )
            
            audio.audio_dir = audio.source_file.path
            audio.save(update_fields=['audio_dir'])

            response_data = {
                'message': 'File uploaded successfully.',
                'audio_id': str(audio.id),
                'status': audio.audio_status,
                'audio_dir': audio.audio_dir,
            }
            return Response(response_data, status=drf_status.HTTP_201_CREATED)

        else:
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
            audio.audio_dir = download_metadata['absolute_path']
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
    data, error = get_status_by_id(id)
    if error:
        return Response({'error': error}, status=drf_status.HTTP_404_NOT_FOUND)
    return Response(data, status=drf_status.HTTP_200_OK)


@api_view(['GET'])
def statuses(request):
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

        send_ws_update(audio.id, 'subtitle_complete', formatted_timelines)

        return Response({'subtitles': formatted_timelines}, status=drf_status.HTTP_200_OK)
    except Exception as exc:
        audio.subtitle_status = Audio.Status.FAILED
        audio.save(update_fields=['subtitle_status'])
        send_ws_update(audio.id, 'subtitle_failed', str(exc))
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

    lock = get_audio_lock(str(id))
    
    try:
        translations = {}
        for i, entry in enumerate(subtitles):
            if entry.get('translate'):
                continue
            subtitle_text = entry.get('subtitle') or entry.get('text')
            if not subtitle_text:
                continue
            
            translation_text = get_translation(subtitle_text)
            translations[i] = translation_text.strip()
            
            send_ws_update(audio.id, 'translation_progress', {
                'index': i,
                'total': len(subtitles),
                'text': translation_text.strip()
            })
    except Exception as exc:
        audio.translation_status = Audio.Status.FAILED
        audio.save(update_fields=['translation_status'])
        send_ws_update(audio.id, 'translation_failed', str(exc))
        return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    with lock:
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
        
        send_ws_update(audio.id, 'translation_complete', subtitles)

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

    lock = get_audio_lock(str(id))
    
    try:
        pronounces = {}
        for i, entry in enumerate(subtitles):
            if entry.get('pronounce'):
                continue
            subtitle_text = entry.get('subtitle') or entry.get('text')
            if not subtitle_text:
                continue
            
            pronounce_text = get_pronunciation(subtitle_text)
            pronounces[i] = pronounce_text.strip()
            
            send_ws_update(audio.id, 'pronounce_progress', {
                'index': i,
                'total': len(subtitles),
                'text': pronounce_text.strip()
            })
    except Exception as exc:
        audio.pronounce_status = Audio.Status.FAILED
        audio.save(update_fields=['pronounce_status'])
        send_ws_update(audio.id, 'pronounce_failed', str(exc))
        return Response({'error': str(exc)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

    with lock:
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
        
        send_ws_update(audio.id, 'pronounce_complete', subtitles)

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