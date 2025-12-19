from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('my/', views.my_documents, name='my_documents'),
    path('all/', views.all_documents, name='all_documents'),
    path('view/<int:document_id>/', views.view_document, name='view_document'),
    path('edit/<int:document_id>/', views.edit_document, name='edit_document'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('submit/<int:document_id>/', views.submit_for_review, name='submit_for_review'),
]
