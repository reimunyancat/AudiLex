from django.urls import path
from .views import transcribe_view, download_audio_view

urlpatterns = [
    path('transcribe/', transcribe_view, name='transcribe'),
    path('audio/download/', download_audio_view, name='download_audio'),
]

