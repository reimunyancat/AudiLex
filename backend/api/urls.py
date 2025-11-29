from django.urls import path
from .views import download_audio, download_list, transcribe, tutor, status, statuses

urlpatterns = [
    # path('download/<str:link>',download_audio, name='download_audio'),
    # path('download_list/',download_list, name='download_list'),
    # path('transcribe/', transcribe, name='transcribe'),
    # path('tutor/<int:id>',tutor,name='tutor'),
    # path('status/<int:id>',status,name='status'),
    # path('statuses/',statuses,name='statuses'),
    path('download_audio/<str:link>/',download_audio, name='download_audio'),
    path('statuses/', statuses, name='statuses'),
    path('status/<str:id>',status,name='status'),
    path('make_subtitle/<str:id>', subtitle, name='subtitle'),
    path('make_pronounce/<str:id>', pronounce, name='pronounce'),
    path('audio_data/<str:id>', audio, name='audio')
]

