from django.db import models

# Create your models here.
class Vidieos(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    download_status = models.BooleanField()
    download_dir = models.TextField()
    transcript_status = models.BooleanField()
    transcript_dir = models.TextField()
    ipa_status = models.BooleanField()
    ipa_dir = models.TextField() 
    translate_status = models.BooleanField()
    translate_dir = models.TextField()