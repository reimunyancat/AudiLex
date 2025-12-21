from django.urls import path
from .views import download_audio, statuses, status, subtitle, translation, pronounce, audio_data, delete_audio

urlpatterns = [
    path('download_audio/', download_audio, name='download_audio'),
    path('statuses/', statuses, name='statuses'),
    path('status/<str:id>', status, name='status'),
    path('make_subtitle/<str:id>', subtitle, name='subtitle'),
    path('make_translation/<str:id>', translation, name='translation'),
    path('make_pronounce/<str:id>', pronounce, name='pronounce'),
    path('audio_data/<str:id>', audio_data, name='audio'),
    path('delete_audio/<str:id>', delete_audio, name='delete_audio'),
]

