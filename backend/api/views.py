import os
import threading
import yt_dlp
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Processing
from .serializers import ProcessingSerializer
from django.conf import settings


def run_download_in_background(job_id):
    """
    Downloads audio in a separate thread and updates the job status.
    """
    try:
        job = Processing.objects.get(pk=job_id)
        job.download_status = Processing.Status.PROCESSING
        job.save()

        os.makedirs(settings.DATA_ROOT, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': {
                'default': str(settings.DATA_ROOT / '%(id)s.%(ext)s')
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(job.youtube_link, download=True)
            filename = os.path.relpath(ydl.prepare_filename(info, outtmpl=str(settings.DATA_ROOT / '%(id)s.%(ext)s')), settings.DATA_ROOT)
            
            job.title = info.get('title', 'Unknown Title')
            job.audio_file_path = filename
            job.download_status = Processing.Status.SUCCESS
            job.save()

    except Exception as e:
        print(f"Error downloading {job_id}: {e}")
        job.download_status = Processing.Status.FAILED
        job.save()


class ProcessingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows processing jobs to be viewed or created.
    """
    queryset = Processing.objects.all().order_by('-created_at')
    serializer_class = ProcessingSerializer

    def create(self, request, *args, **kwargs):
        """
        Starts a new download job.
        Expects {'youtube_link': '...'} in the request body.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        job = serializer.instance
        
        thread = threading.Thread(target=run_download_in_background, args=(job.id,))
        thread.start()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
