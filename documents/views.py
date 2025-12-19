from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from .forms import DocumentUploadForm
from .models import Document
from activity.models import ActivityLog

@login_required
def upload_document(request):
    if not request.user.can_upload_document():
        raise PermissionDenied("You do not have permission to upload documents")
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.status = 'DRAFT'
            document.save()

            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='UPLOAD'
            )
            messages.success(request, "Document uploaded successfully as draft.")
            return redirect('my_documents')
    else:
        form = DocumentUploadForm()

    return render(request, 'documents/upload.html', {'form': form})

@login_required
def my_documents(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    documents_qs = Document.objects.filter(
        uploaded_by=request.user,
        is_deleted=False
    )
    
    documents_qs = documents_qs.order_by('-created_at')

    if search_query:
        documents_qs = documents_qs.filter(title__icontains=search_query)

    if status_filter:
        documents_qs = documents_qs.filter(status=status_filter)

    paginator = Paginator(documents_qs, 10)
    page_number = request.GET.get("page")
    documents_page = paginator.get_page(page_number)

    return render(
        request,
        'documents/my_documents.html',
        {
            'documents': documents_page,
            'search_query': search_query,
            'status_filter': status_filter,
        }
    )

@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, is_deleted=False)
    
    if not request.user.can_view_document(document):
        raise PermissionDenied("You do not have permission to view this document")
    
    ActivityLog.objects.create(
        user=request.user,
        document=document,
        action='VIEW'
    )
    
    # Get assigned reviewer if document is in review
    assigned_task = None
    if document.status == 'REVIEW':
        from workflows.models import Task
        assigned_task = Task.objects.filter(
            document=document,
            status='PENDING'
        ).select_related('assigned_to').first()
    
    return render(request, 'documents/view_document.html', {
        'document': document,
        'assigned_task': assigned_task
    })

@login_required
def edit_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, is_deleted=False)
    
    if not request.user.can_edit_document(document):
        messages.error(
            request,
            f"You cannot edit this document. Documents can only be edited in DRAFT or REJECTED status. "
            f"Current status: {document.get_status_display()}"
        )
        return redirect('my_documents')
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            if document.status == 'REJECTED':
                document.status = 'DRAFT'
            document.save()
            
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='UPDATE'
            )
            messages.success(request, "Document updated successfully.")
            return redirect('my_documents')
    else:
        form = DocumentUploadForm(instance=document)
    
    return render(request, 'documents/edit_document.html', {
        'form': form,
        'document': document
    })

@login_required
def submit_for_review(request, document_id):
    document = get_object_or_404(Document, id=document_id, is_deleted=False)
    
    try:
        if document.uploaded_by != request.user and not request.user.is_admin():
            raise PermissionDenied("Only the document owner can submit for review")
        
        if not document.can_be_submitted_for_review():
            raise ValidationError(
                f"Document in {document.get_status_display()} status cannot be submitted for review"
            )
        
        document.submit_for_review(request.user)
        
        ActivityLog.objects.create(
            user=request.user,
            document=document,
            action='UPDATE'
        )
        
        messages.success(request, "Document submitted for review successfully.")
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, str(e))
    
    return redirect('my_documents')

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, is_deleted=False)
    
    if not request.user.can_delete_document(document):
        messages.error(
            request,
            f"You cannot delete this document. Documents can only be deleted in DRAFT or REJECTED status. "
            f"Current status: {document.get_status_display()}"
        )
        return redirect('my_documents')

    document.is_deleted = True
    document.save()

    ActivityLog.objects.create(
        user=request.user,
        action='DELETE',
        document=document,
        description=f"Deleted document: {document.title}"
    )
    messages.success(request, "Document deleted successfully.")
    return redirect('my_documents')

@login_required
def all_documents(request):
    if not request.user.is_admin() and not request.user.is_reviewer():
        raise PermissionDenied("You do not have permission to view all documents")
    
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    
    documents_qs = Document.objects.filter(is_deleted=False).select_related('uploaded_by').order_by('-created_at')
    
    if search_query:
        documents_qs = documents_qs.filter(title__icontains=search_query)
    
    if status_filter:
        documents_qs = documents_qs.filter(status=status_filter)
    
    paginator = Paginator(documents_qs, 10)
    page_number = request.GET.get("page")
    documents_page = paginator.get_page(page_number)
    
    # Get assigned tasks for documents in REVIEW status
    from workflows.models import Task
    review_doc_ids = [doc.id for doc in documents_page if doc.status == 'REVIEW']
    assigned_tasks = {}
    if review_doc_ids:
        tasks = Task.objects.filter(
            document_id__in=review_doc_ids,
            status='PENDING'
        ).select_related('assigned_to')
        assigned_tasks = {task.document_id: task for task in tasks}
    
    return render(request, 'documents/all_documents.html', {
        'documents': documents_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'assigned_tasks': assigned_tasks,
    })
