import threading
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Processing
from .serializers import ProcessingSerializer
from functions.audio import download_audio

class ProcessingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows processing jobs to be viewed or created.
    """
    authentication_classes = []
    queryset = Processing.objects.all().order_by('-created_at')
    serializer_class = ProcessingSerializer

    def create(self, request, *args, **kwargs):
        """
        Starts a new download job or restarts a failed one.
        Expects {'youtube_link': '...'} in the request body.
        """
        youtube_link = request.data.get('youtube_link')
        if not youtube_link:
            return Response({'youtube_link': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        existing_job = Processing.objects.filter(youtube_link=youtube_link).first()

        if existing_job:
            # If a failed job exists, restart it
            if existing_job.download_status == Processing.Status.FAILED or \
               existing_job.transcript_status == Processing.Status.FAILED:
                
                existing_job.download_status = Processing.Status.PENDING
                existing_job.transcript_status = Processing.Status.PENDING
                existing_job.save()
                
                thread = threading.Thread(target=download_audio, args=(existing_job.id,))
                thread.start()
                
                serializer = self.get_serializer(existing_job)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
            else:
                # Job is already PENDING or SUCCESS, return existing data
                serializer = self.get_serializer(existing_job)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
        
        # No existing job, create a new one
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        job = serializer.instance
        
        thread = threading.Thread(target=download_audio, args=(job.id,))
        thread.start()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
