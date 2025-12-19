from django.urls import path
from .views import notifications_list, notifications_mark_all_read

urlpatterns = [
    path("", notifications_list, name="notifications_list"),
    path("mark-all-read/", notifications_mark_all_read, name="notifications_mark_all_read"),
]



