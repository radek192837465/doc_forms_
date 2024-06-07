# models.py

from django.db import models
import uuid
class UploadedFile(models.Model):
    file_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file_name = models.CharField(max_length=250)
    file_describe = models.CharField(max_length=250)
    json_content = models.JSONField()
