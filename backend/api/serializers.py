from rest_framework import serializers
from .models import Audio


class ProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audio
        fields = [
            'id',
            'youtube_link',
            'youtube_title',
            'source_file',
            'audio_dir',
            'audio_status',
            'audio_data',
            'subtitle_status',
            'translation_status',
            'pronounce_status',
        ]