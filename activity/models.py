from django.db import models
from django.conf import settings
from documents.models import Document

User = settings.AUTH_USER_MODEL

class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('UPLOAD', 'Upload'),
        ('UPDATE', 'Update'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.document}"