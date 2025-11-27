from django.db import models

class Processing(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', '대기 중'
        PROCESSING = 'PROCESSING', '처리 중'
        SUCCESS = 'SUCCESS', '성공'
        FAILED = 'FAILED', '실패'

    youtube_link = models.URLField(max_length=500, unique=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    download_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    audio_file_path = models.CharField(max_length=512, blank=True, null=True)
    transcript_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transcript = models.JSONField(blank=True, null=True)
    ipa_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    ipa = models.TextField(blank=True, null=True)
    translate_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    translation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title or self.id}"