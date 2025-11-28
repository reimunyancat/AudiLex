from rest_framework import serializers
from .models import Processing


class ProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processing
        fields = [
            'id', 'youtube_link', 'title', 'created_at',
            'download_status', 'audio_file_path',
            'transcript_status', 'transcript',
            'ipa_status', 'ipa',
            'translate_status', 'translation'
        ]