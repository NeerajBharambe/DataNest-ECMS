from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import DocumentVersion
from documents.models import Document


@login_required
def document_versions(request, document_id):
    document = get_object_or_404(
        Document, id=document_id, uploaded_by=request.user, is_deleted=False
    )
    versions = DocumentVersion.objects.filter(document=document).order_by(
        "-version_number"
    )
    return render(
        request,
        "versions/document_versions.html",
        {"document": document, "versions": versions},
    )
