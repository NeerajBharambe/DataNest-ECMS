from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from documents.models import Document
from .serializers import DocumentSerializer

class DocumentListCreateAPI(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)