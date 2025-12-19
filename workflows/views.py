from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from .models import Task, Workflow
from documents.models import Document
from activity.models import ActivityLog

@login_required
def my_tasks(request):
    if not request.user.is_reviewer() and not request.user.is_admin():
        raise PermissionDenied("You do not have permission to access review tasks")
    
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    tasks_qs = Task.objects.filter(
        assigned_to=request.user
    ).select_related('document', 'document__uploaded_by')

    if status_filter:
        tasks_qs = tasks_qs.filter(status=status_filter)
    else:
        tasks_qs = tasks_qs.filter(status='PENDING')

    if search_query:
        tasks_qs = tasks_qs.filter(document__title__icontains=search_query)

    tasks_qs = tasks_qs.order_by('-created_at')

    paginator = Paginator(tasks_qs, 10)
    page_number = request.GET.get("page")
    tasks_page = paginator.get_page(page_number)

    return render(
        request,
        'workflows/my_tasks.html',
        {
            'tasks': tasks_page,
            'search_query': search_query,
            'status_filter': status_filter
        }
    )


@login_required
def review_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if task.assigned_to != request.user and not request.user.is_admin():
        raise PermissionDenied("You are not assigned to this task")
    
    if task.document.uploaded_by == request.user:
        raise PermissionDenied(
            "You cannot review your own document (separation of duties)"
        )
    
    if not request.user.can_review_document(task.document):
        raise PermissionDenied("You do not have permission to review this document")
    
    if task.status != 'PENDING':
        messages.warning(request, f"This task has already been {task.status.lower()}")
        return redirect('my_tasks')

    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '').strip()

        try:
            if action == 'APPROVED':
                task.approve(request.user, comments)
                messages.success(request, "Document approved successfully.")
                
                ActivityLog.objects.create(
                    user=request.user,
                    document=task.document,
                    action='APPROVED'
                )
            elif action == 'REJECTED':
                if not comments:
                    messages.error(request, "Comments are required when rejecting a document")
                    return render(request, 'workflows/review_task.html', {'task': task})
                
                task.reject(request.user, comments)
                messages.success(request, "Document rejected successfully.")
                
                ActivityLog.objects.create(
                    user=request.user,
                    document=task.document,
                    action='REJECTED'
                )
            else:
                messages.error(request, "Invalid action")
                return render(request, 'workflows/review_task.html', {'task': task})
            
            return redirect('my_tasks')
        except (PermissionDenied, ValidationError) as e:
            messages.error(request, str(e))

    return render(
        request,
        'workflows/review_task.html',
        {'task': task}
    )


@login_required
def assign_reviewer(request, document_id):
    if not request.user.is_admin():
        raise PermissionDenied("Only admins can assign reviewers")
    
    document = get_object_or_404(Document, id=document_id, is_deleted=False)
    
    if document.status != 'REVIEW':
        messages.error(request, "Document must be in review status to assign a reviewer")
        return redirect('all_documents')
    
    if request.method == 'POST':
        reviewer_id = request.POST.get('reviewer_id')
        workflow_id = request.POST.get('workflow_id')
        
        try:
            from accounts.models import User
            reviewer = User.objects.get(id=reviewer_id)
            
            if reviewer == document.uploaded_by:
                raise ValidationError(
                    "Cannot assign document owner as reviewer (separation of duties)"
                )
            
            if not reviewer.is_reviewer() and not reviewer.is_admin():
                raise ValidationError("Selected user is not a reviewer")
            
            workflow = Workflow.objects.get(id=workflow_id) if workflow_id else None
            if not workflow:
                workflow = Workflow.objects.create(
                    name=f"Review for {document.title}",
                    created_by=request.user,
                    is_active=True
                )
            
            Task.objects.create(
                workflow=workflow,
                document=document,
                assigned_to=reviewer,
                status='PENDING'
            )
            
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='UPDATE'
            )
            
            messages.success(request, f"Reviewer {reviewer.username} assigned successfully")
            return redirect('all_documents')
            
        except (User.DoesNotExist, Workflow.DoesNotExist, ValidationError) as e:
            messages.error(request, str(e))
    
    from accounts.models import User
    reviewers = User.objects.filter(role__in=['REVIEWER', 'ADMIN']).exclude(
        id=document.uploaded_by.id
    )
    workflows = Workflow.objects.filter(is_active=True)
    
    return render(request, 'workflows/assign_reviewer.html', {
        'document': document,
        'reviewers': reviewers,
        'workflows': workflows
    })


@login_required
def pending_reviews(request):
    if not request.user.is_reviewer() and not request.user.is_admin():
        raise PermissionDenied("You do not have permission to view pending reviews")
    
    search_query = request.GET.get("q", "").strip()
    
    documents_qs = Document.objects.filter(
        status='REVIEW',
        is_deleted=False
    ).exclude(
        uploaded_by=request.user
    ).select_related('uploaded_by')
    
    if search_query:
        documents_qs = documents_qs.filter(title__icontains=search_query)
    
    documents_qs = documents_qs.order_by('-submitted_for_review_at')
    
    paginator = Paginator(documents_qs, 10)
    page_number = request.GET.get("page")
    documents_page = paginator.get_page(page_number)
    
    # Get assigned tasks for documents in the page
    review_doc_ids = [doc.id for doc in documents_page]
    assigned_tasks = {}
    if review_doc_ids:
        tasks = Task.objects.filter(
            document_id__in=review_doc_ids,
            status='PENDING'
        ).select_related('assigned_to')
        assigned_tasks = {task.document_id: task for task in tasks}
    
    return render(request, 'workflows/pending_reviews.html', {
        'documents': documents_page,
        'search_query': search_query,
        'assigned_tasks': assigned_tasks,
    })
