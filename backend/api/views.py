import os
import threading
import base64
import mimetypes
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Audio
from .functions.audio import download_audio as process_audio_download
from .functions.subtitle import STTModel
from .functions.preprocess import PreprocessModel


stt_model = STTModel()
preprocess_model = PreprocessModel()


@api_view(['POST'])
def download_audio(request, link):
    """
    API endpoint to download audio from a YouTube video.
    """
    if request.method == 'POST':
        video_url = request.data.get('video_url')
        if not video_url:
            return Response({'error': 'video_url is required'}, status=status.HTTP_400_BAD_REQUEST)

        audio = Audio.objects.create(
            youtube_link=video_url,
            youtube_title='',
            audio_name='pending',
            audio_dir='',
        )

        threading.Thread(
            target=process_audio_download,
            args=(audio.id,),
            daemon=True,
        ).start()

        response_data = {
            'message': 'Audio job created. Processing in background.',
            'audio_id': str(audio.id),
            'status': audio.audio_status,
        }
        return Response(response_data, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def status(request):
    """
    받은 id의 transcribe, ipa, translate의 상황(진행 안됨, 진행중, 완료) 조회
    """

@api_view(['GET'])
def statuses(request):
    """
    모든 transcribe, ipa, translate 상황 조회
    """

@api_view(['GET'])
def subtitle(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_path = audio.audio_dir
    if not audio_path:
        return Response({'error': 'audio_dir is not set for this audio record.'}, status=status.HTTP_400_BAD_REQUEST)

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(settings.BASE_DIR, audio_path.lstrip('/'))

    if not os.path.exists(audio_path):
        return Response({'error': f'audio file not found at {audio_path}'}, status=status.HTTP_404_NOT_FOUND)

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

        return Response({'subtitles': formatted_timelines}, status=status.HTTP_200_OK)
    except Exception as exc:
        audio.subtitle_status = Audio.Status.FAILED
        audio.save(update_fields=['subtitle_status'])
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def translation(request, id):
    #id에서 audio_data를 찾음
    # audio_data에서 1 ~ 까지의 subtitle을 읽어 translation을 내보냄
    # 받은 translation을 추가해서 저장함
    ...

@api_view(['GET'])
def pronounce(request, id):
    #id에서 audio_data를 찾음
    # audio_data에서 1 ~ 까지의 subtitle을 읽어 히라가나를 내보냄
    # 받은 translation을 추가해서 저장함
    ...

@api_view(['GET'])
def audio_data(request, id):
    audio = get_object_or_404(Audio, pk=id)

    audio_path = audio.audio_dir
    if not audio_path:
        return Response({'error': 'audio_dir is not set for this record.'}, status=status.HTTP_400_BAD_REQUEST)

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(settings.BASE_DIR, audio_path.lstrip('/'))

    if not os.path.exists(audio_path):
        return Response({'error': f'audio file not found at {audio_path}'}, status=status.HTTP_404_NOT_FOUND)

    try:
        with open(audio_path, 'rb') as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')
    except OSError as exc:
        return Response({'error': f'failed to read audio file: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        status=status.HTTP_200_OK,
    )
