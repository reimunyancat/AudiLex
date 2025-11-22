from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def transcribe_view(request):
    """
    API endpoint to transcribe a YouTube video.
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

