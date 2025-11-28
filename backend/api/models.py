import uuid

from django.db import models


class Audio(models.Model):
    """Represents an audio asset and the processing lifecycle of derived data."""

    STATUS_PROCESSING = "Processing"
    STATUS_FINISHED = "Finished"
    STATUS_NOT_PROCESSED = "Not Processed"
    STATUS_CHOICES = [
        (STATUS_PROCESSING, STATUS_PROCESSING),
        (STATUS_FINISHED, STATUS_FINISHED),
        (STATUS_NOT_PROCESSED, STATUS_NOT_PROCESSED),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_name = models.CharField(max_length=255)
    audio_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_PROCESSED)
    audio_dir = models.TextField(blank=True)
    audio_data = models.TextField(blank=True)
    audio_data_dir = models.TextField(blank=True)
    subtitle_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_PROCESSED)
    translation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_PROCESSED)
    pronounce_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_PROCESSED)

    def __str__(self) -> str:
        return self.audio_name