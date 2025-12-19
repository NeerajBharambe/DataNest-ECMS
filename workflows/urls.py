from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/<int:task_id>/', views.review_task, name='review_task'),
    path('pending-reviews/', views.pending_reviews, name='pending_reviews'),
    path('assign-reviewer/<int:document_id>/', views.assign_reviewer, name='assign_reviewer'),
]
