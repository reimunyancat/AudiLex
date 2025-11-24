from django.urls import path
from .views import transcribe, download_audio

urlpatterns = [
    path('transcribe/', transcribe, name='transcribe'),
    path('audio/download/', download_audio, name='download_audio'),
]

