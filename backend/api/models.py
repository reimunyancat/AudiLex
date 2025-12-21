from django.db import models
import uuid

def default_audio_data():
    return {"data": []}


class Audio(models.Model):
    class Status(models.TextChoices):
        NOT_PROCESSED = 'Not Processed', 'Not Processed'
        PROCESSING = 'Processing', 'Processing'
        FINISHED = 'Finished', 'Finished'
        FAILED = 'Failed', 'Failed'
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    youtube_link = models.URLField(blank=True, null=True)
    youtube_title = models.CharField(max_length=255, blank=True, null=True)
    source_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    audio_dir = models.CharField(max_length=512, blank=True, null=True)
    audio_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    audio_data = models.JSONField(default=default_audio_data, blank=True)
    subtitle_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    translation_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    pronounce_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)

    def __str__(self):
        return f"{self.audio_name} ({self.id})"