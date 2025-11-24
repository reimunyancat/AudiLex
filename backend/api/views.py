from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from audio import process as download_process

@api_view(['POST'])
def transcribe(request):
    """
    이제 여기서 다운받은 mp3가지고 응땅하면됨
    """
    if request.method == 'POST':
        video_url = request.data.get('video_url')
        if not video_url:
            return Response({'error': 'video_url is required'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO
        
        response_data = {
            'message': 'Transcription process started.',
            'video_url': video_url,
        }
        return Response(response_data, status=status.HTTP_200_OK)

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
            download_process(video_url, settings.MEDIA_ROOT)
            
            response_data = {
                'message': 'Audio download completed successfully.',
                'video_url': video_url,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
