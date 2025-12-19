from django.urls import path
from .views import DocumentListCreateAPI

urlpatterns = [
    path('documents/', DocumentListCreateAPI.as_view()),
]