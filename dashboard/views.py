from django.shortcuts import render
from documents.models import Document
from audit.models import AuditTrail
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    total_documents = Document.objects.count()
    approved_documents = Document.objects.filter(status='APPROVED').count()
    rejected_documents = Document.objects.filter(status='REJECTED').count()
    pending_documents = Document.objects.filter(status='REVIEW').count()

    recent_activities = AuditTrail.objects.order_by('-timestamp')[:10]

    context = {
        'total_documents': total_documents,
        'approved_documents': approved_documents,
        'rejected_documents': rejected_documents,
        'pending_documents': pending_documents,
        'recent_activities': recent_activities,
    }

    return render(request, 'dashboard/dashboard.html', context)
