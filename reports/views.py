from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from documents.models import Document


@login_required
def reports_dashboard(request):
    total_documents = Document.objects.count()
    approved_documents = Document.objects.filter(status="APPROVED").count()
    rejected_documents = Document.objects.filter(status="REJECTED").count()
    pending_documents = Document.objects.filter(status="REVIEW").count()

    return render(
        request,
        "reports/reports_dashboard.html",
        {
            "total_documents": total_documents,
            "approved_documents": approved_documents,
            "rejected_documents": rejected_documents,
            "pending_documents": pending_documents,
        },
    )
