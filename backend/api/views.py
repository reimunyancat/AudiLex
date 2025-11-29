import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .models import Audio
from backend.api.functions.subtitle import STTmodel
from functions.audio import download_audio


model = STTmodel()


@api_view(['POST'])
def download_audio(request):
    """
    API endpoint to download audio from a YouTube video.
    """
    if request.method == 'POST':
        video_url = request.data.get('video_url')
        if not video_url:
            return Response({'error': 'video_url is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            download_audio(video_url, settings.MEDIA_ROOT)
            
            response_data = {
                'message': 'Audio download completed successfully.',
                'video_url': video_url,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
def subtitle(request):
    ...

@api_view(['GET'])
def translation(request):
    ...

@api_view(['GET'])
def pronounce(request):
    ...

@api_view(['GET'])
def audio_data(request):
    ...
