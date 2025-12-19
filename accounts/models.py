from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('REVIEWER', 'Reviewer'),
        ('USER', 'User'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_reviewer(self):
        return self.role == 'REVIEWER'

    def is_regular_user(self):
        return self.role == 'USER'

    def can_view_document(self, document):
        if self.is_admin():
            return True
        if self.is_reviewer():
            return True
        return document.uploaded_by == self

    def can_edit_document(self, document):
        if self.is_admin():
            return True
        if document.uploaded_by == self:
            return document.status in ['DRAFT', 'REJECTED']
        return False

    def can_delete_document(self, document):
        if self.is_admin():
            return True
        if document.uploaded_by == self:
            return document.status in ['DRAFT', 'REJECTED']
        return False

    def can_upload_document(self):
        return self.role in ['ADMIN', 'REVIEWER', 'USER']

    def can_review_document(self, document):
        if not self.is_reviewer() and not self.is_admin():
            return False
        if document.uploaded_by == self:
            return False
        return True

    def can_approve_document(self, document):
        return self.can_review_document(document)

    def can_override_status(self):
        return self.is_admin()
