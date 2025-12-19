from django.urls import path
from .views import MyTasksAPI, ReviewTaskAPI

urlpatterns = [
    path('tasks/', MyTasksAPI.as_view()),
    path('tasks/<int:pk>/review/', ReviewTaskAPI.as_view()),
]
