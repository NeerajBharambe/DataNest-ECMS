from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from folders.models import Folder, Category

User = settings.AUTH_USER_MODEL


class Document(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ARCHIVED', 'Archived'),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    submitted_for_review_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def can_be_edited(self):
        return self.status in ['DRAFT', 'REJECTED']

    def can_be_submitted_for_review(self):
        return self.status in ['DRAFT', 'REJECTED']

    def can_be_reviewed(self):
        return self.status == 'REVIEW'

    def validate_status_transition(self, new_status, user):
        if user.can_override_status():
            return True

        if self.status == 'DRAFT' and new_status == 'REVIEW':
            if self.uploaded_by != user:
                raise PermissionDenied("Only the document owner can submit for review")
            return True
        elif self.status == 'REVIEW' and new_status in ['APPROVED', 'REJECTED']:
            if not user.can_review_document(self):
                raise PermissionDenied("You cannot review this document")
            return True
        elif self.status == 'REJECTED' and new_status in ['DRAFT', 'REVIEW']:
            if self.uploaded_by != user:
                raise PermissionDenied("Only the document owner can resubmit")
            return True
        elif user.is_admin():
            return True
        else:
            raise ValidationError(f"Invalid status transition from {self.status} to {new_status}")

    def submit_for_review(self, user):
        if not self.can_be_submitted_for_review():
            raise ValidationError(f"Document in {self.status} status cannot be submitted for review")
        if self.uploaded_by != user and not user.is_admin():
            raise PermissionDenied("Only the document owner can submit for review")
        
        from django.utils import timezone
        self.status = 'REVIEW'
        self.submitted_for_review_at = timezone.now()
        self.save()

    def update_status(self):
        tasks = self.workflow_tasks.all()

        if tasks.filter(status='REJECTED').exists():
            self.status = 'REJECTED'
        elif tasks.exists() and all(task.status == 'APPROVED' for task in tasks):
            self.status = 'APPROVED'
        elif tasks.exists():
            self.status = 'REVIEW'
        else:
            self.status = 'DRAFT'

        super().save(update_fields=['status'])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = Document.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Document.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

        from versions.models import DocumentVersion
        from audit.models import AuditTrail

        if is_new:
            version_number = 1
            DocumentVersion.objects.create(
                document=self,
                file=self.file,
                version_number=version_number,
                created_by=self.uploaded_by
            )
            AuditTrail.objects.create(
                user=self.uploaded_by,
                document=self,
                action='UPLOAD',
                description=f"Document uploaded with status: {self.status}"
            )
        else:
            last_version = self.versions.order_by('-version_number').first()
            version_number = last_version.version_number + 1 if last_version else 1

            DocumentVersion.objects.create(
                document=self,
                file=self.file,
                version_number=version_number,
                created_by=self.uploaded_by
            )

            if old_status and old_status != self.status:
                AuditTrail.objects.create(
                    user=self.reviewed_by if self.reviewed_by else self.uploaded_by,
                    document=self,
                    action='UPDATE',
                    description=f"Document status changed from {old_status} to {self.status}"
                )
            else:
                AuditTrail.objects.create(
                    user=self.uploaded_by,
                    document=self,
                    action='UPDATE',
                    description="Document updated"
                )


class Metadata(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='metadata'
    )
    attribute_name = models.CharField(max_length=100)
    attribute_value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value}"
