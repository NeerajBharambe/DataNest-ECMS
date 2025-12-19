from django.urls import path
from .views import document_versions

urlpatterns = [
    path("<int:document_id>/", document_versions, name="document_versions"),
]


