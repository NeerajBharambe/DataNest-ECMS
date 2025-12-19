from django.core.exceptions import PermissionDenied


class DocumentPermissionMixin:
    """
    Mixin to handle document permissions in views
    """
    
    def check_document_view_permission(self, request, document):
        """Check if user can view the document"""
        if not request.user.can_view_document(document):
            raise PermissionDenied("You do not have permission to view this document")
    
    def check_document_edit_permission(self, request, document):
        """Check if user can edit the document"""
        if not request.user.can_edit_document(document):
            raise PermissionDenied(
                f"You cannot edit this document. Documents can only be edited in DRAFT or REJECTED status. "
                f"Current status: {document.status}"
            )
    
    def check_document_delete_permission(self, request, document):
        """Check if user can delete the document"""
        if not request.user.can_delete_document(document):
            raise PermissionDenied(
                f"You cannot delete this document. Documents can only be deleted in DRAFT or REJECTED status. "
                f"Current status: {document.status}"
            )
    
    def check_document_upload_permission(self, request):
        """Check if user can upload documents"""
        if not request.user.can_upload_document():
            raise PermissionDenied("You do not have permission to upload documents")
    
    def check_document_review_permission(self, request, document):
        """Check if user can review the document"""
        if not request.user.can_review_document(document):
            if document.uploaded_by == request.user:
                raise PermissionDenied(
                    "You cannot review your own document (separation of duties)"
                )
            raise PermissionDenied("You do not have permission to review this document")
    
    def check_document_submit_permission(self, request, document):
        """Check if user can submit document for review"""
        if document.uploaded_by != request.user and not request.user.is_admin():
            raise PermissionDenied("Only the document owner can submit for review")
        
        if not document.can_be_submitted_for_review():
            raise PermissionDenied(
                f"Document in {document.status} status cannot be submitted for review"
            )


def require_document_permission(permission_type):
    """
    Decorator to check document permissions
    Usage:
        @require_document_permission('view')
        @require_document_permission('edit')
        @require_document_permission('delete')
        @require_document_permission('review')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            from documents.models import Document
            from django.shortcuts import get_object_or_404
            
            document_id = kwargs.get('document_id') or kwargs.get('pk')
            if not document_id:
                raise ValueError("Document ID not found in view kwargs")
            
            document = get_object_or_404(Document, id=document_id, is_deleted=False)
            
            if permission_type == 'view':
                if not request.user.can_view_document(document):
                    raise PermissionDenied("You do not have permission to view this document")
            elif permission_type == 'edit':
                if not request.user.can_edit_document(document):
                    raise PermissionDenied(
                        f"You cannot edit this document. Current status: {document.status}"
                    )
            elif permission_type == 'delete':
                if not request.user.can_delete_document(document):
                    raise PermissionDenied(
                        f"You cannot delete this document. Current status: {document.status}"
                    )
            elif permission_type == 'review':
                if not request.user.can_review_document(document):
                    if document.uploaded_by == request.user:
                        raise PermissionDenied(
                            "You cannot review your own document (separation of duties)"
                        )
                    raise PermissionDenied("You do not have permission to review this document")
            
            kwargs['document'] = document
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
