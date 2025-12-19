from django.urls import path
from .views import folders_list, create_folder, create_category

urlpatterns = [
    path("", folders_list, name="folders_list"),
    path("create-folder/", create_folder, name="create_folder"),
    path("create-category/", create_category, name="create_category"),
]



