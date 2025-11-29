from django.db import models
import uuid

def default_audio_data():
    return {"data": []}
    """
    ex
    {
    data: [
        {
        "index":1
        "start":13.0
        "end":16.2
        "subtitle":asdfasfas
        "pronounce":asdfasd
        "translate":asdfas
        },
        {
        "index":2
        "start": 75.6
        "end": 1738.6
        "subtitle":asdfasfasasf
        "pronounce":asdfasdasdf
        "translate":asdfasasdf
        },
    ]
    }
    """


class Audio(models.Model):
    class Status(models.TextChoices):
        NOT_PROCESSED = 'Not Processed', 'Not Processed'
        PROCESSING = 'Processing', 'Processing'
        FINISHED = 'Finished', 'Finished'
        FAILED = 'Failed', 'Failed'
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    youtube_link = models.URLField()
    youtube_title = models.CharField(max_length=255)
    audio_dir = models.CharField(max_length=512)
    audio_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    audio_data = models.JSONField(default=default_audio_data, blank=True)
    subtitle_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    translation_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)
    pronounce_status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_PROCESSED)

    def __str__(self):
        return f"{self.audio_name} ({self.id})"