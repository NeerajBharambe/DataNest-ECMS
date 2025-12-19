from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from documents.models import Document

User = settings.AUTH_USER_MODEL


class Workflow(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_workflows'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='workflow_tasks'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.document.title} - {self.status}"

    def clean(self):
        super().clean()
        if self.assigned_to == self.document.uploaded_by:
            raise ValidationError({
                'assigned_to': 'A reviewer cannot be assigned to review their own document (separation of duties)'
            })
        
        if not self.assigned_to.is_reviewer() and not self.assigned_to.is_admin():
            raise ValidationError({
                'assigned_to': 'Only users with Reviewer or Admin role can be assigned review tasks'
            })

    def approve(self, reviewer, comments=''):
        if reviewer != self.assigned_to and not reviewer.is_admin():
            raise PermissionDenied("You are not assigned to this task")
        
        if reviewer == self.document.uploaded_by:
            raise PermissionDenied("You cannot approve your own document (separation of duties)")
        
        if not reviewer.can_review_document(self.document):
            raise PermissionDenied("You do not have permission to review this document")
        
        from django.utils import timezone
        self.status = 'APPROVED'
        self.comments = comments
        self.completed_at = timezone.now()
        self.save()

    def reject(self, reviewer, comments=''):
        if reviewer != self.assigned_to and not reviewer.is_admin():
            raise PermissionDenied("You are not assigned to this task")
        
        if reviewer == self.document.uploaded_by:
            raise PermissionDenied("You cannot reject your own document (separation of duties)")
        
        if not reviewer.can_review_document(self.document):
            raise PermissionDenied("You do not have permission to review this document")
        
        if not comments:
            raise ValidationError("Comments are required when rejecting a document")
        
        from django.utils import timezone
        self.status = 'REJECTED'
        self.comments = comments
        self.completed_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = Task.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Task.DoesNotExist:
                pass
        
        self.full_clean()
        
        super().save(*args, **kwargs)

        if old_status != self.status and self.status in ['APPROVED', 'REJECTED']:
            from django.utils import timezone
            self.document.reviewed_by = self.assigned_to
            self.document.reviewed_at = timezone.now()
            self.document.review_comments = self.comments
            self.document.update_status()

        from notifications.models import Notification
        from audit.models import AuditTrail

        if is_new:
            message = f"You have been assigned to review document '{self.document.title}'"
            Notification.objects.create(
                user=self.assigned_to,
                document=self.document,
                message=message,
                notification_type='TASK'
            )
            AuditTrail.objects.create(
                user=self.assigned_to,
                document=self.document,
                action='UPDATE',
                description=f"Review task assigned to {self.assigned_to.username}"
            )
        elif old_status != self.status:
            if self.status == 'APPROVED':
                message = f"Your document '{self.document.title}' has been approved by {self.assigned_to.username}"
                action = 'APPROVED'
            elif self.status == 'REJECTED':
                message = f"Your document '{self.document.title}' has been rejected by {self.assigned_to.username}"
                action = 'REJECTED'
            else:
                message = f"Review status updated for document '{self.document.title}'"
                action = 'UPDATE'

            Notification.objects.create(
                user=self.document.uploaded_by,
                document=self.document,
                message=message,
                notification_type='TASK'
            )

            AuditTrail.objects.create(
                user=self.assigned_to,
                document=self.document,
                action=action,
                description=f"Document {self.status.lower()} by {self.assigned_to.username}. Comments: {self.comments[:100]}"
            )
