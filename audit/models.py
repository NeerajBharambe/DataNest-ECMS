from django.db import models
from django.conf import settings
from documents.models import Document

User = settings.AUTH_USER_MODEL


class AuditTrail(models.Model):
    ACTION_CHOICES = (
        ('UPLOAD', 'Upload'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('DOWNLOAD', 'Download'),
        ('VIEW', 'View'),
        ('SUBMIT_REVIEW', 'Submit for Review'),
        ('ASSIGN_REVIEWER', 'Assign Reviewer'),
        ('STATUS_CHANGE', 'Status Change'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['document', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"