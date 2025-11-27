import os
import threading
import requests
import yt_dlp
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Processing
from .serializers import ProcessingSerializer
from django.conf import settings


def download_audio(job_id):
    """
    Downloads audio in a separate thread and updates the job status.
    """
    try:
        job = Processing.objects.get(pk=job_id)
        job.download_status = Processing.Status.PROCESSING
        job.save()

        audio_dir = settings.DATA_ROOT / 'audio'
        os.makedirs(audio_dir, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(audio_dir / '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(job.youtube_link, download=True)
            
            final_filename = ydl.prepare_filename(info)
            video_id = info.get('id')
            final_mp3_path = audio_dir / f"{video_id}.mp3"
            
            filename_for_db = os.path.relpath(final_mp3_path, settings.DATA_ROOT)

            job.title = info.get('title', 'Unknown Title')
            job.audio_file_path = filename_for_db
            job.download_status = Processing.Status.SUCCESS
            job.save()

            print(f"Download complete. Sending to STT server for transcription: {job.id}...")
            
            transcript_dir = settings.DATA_ROOT / 'transcript'
            os.makedirs(transcript_dir, exist_ok=True)
            
            # Call external STT server
            try:
                # Open the audio file in binary mode for sending
                with open(final_mp3_path, 'rb') as audio_file:
                    files = {'audio': (audio_file.name, audio_file, 'audio/mpeg')}
                    stt_response = requests.post(
                        f"{settings.STT_SERVER_URL}/transcribe",
                        files=files,
                        timeout=3600
                    )
                stt_response.raise_for_status()
                transcription_result = stt_response.json()

                # Update job with transcription result
                job.transcript = transcription_result['text']
                job.transcript_status = Processing.Status.SUCCESS
                job.save()
                print(f"Transcription complete for {job.id}.")

            except requests.exceptions.RequestException as req_e:
                print(f"Error communicating with STT server for {job.id}: {req_e}")
                job.transcript_status = Processing.Status.FAILED
                job.save()
            except Exception as e:
                print(f"Error processing transcription result for {job.id}: {e}")
                job.transcript_status = Processing.Status.FAILED
                job.save()


    except Exception as e:
        print(f"Error processing {job_id}: {e}")
        job.download_status = Processing.Status.FAILED
        job.save()


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
