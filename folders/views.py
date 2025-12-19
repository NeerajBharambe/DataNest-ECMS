from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Folder, Category
from accounts.decorators import role_required


@login_required
@role_required("ADMIN", "EDITOR")
def folders_list(request):
    folders = Folder.objects.filter(created_by=request.user, parent__isnull=True)
    categories = Category.objects.all()
    return render(
        request,
        "folders/folders_list.html",
        {"folders": folders, "categories": categories},
    )


@login_required
@role_required("ADMIN", "EDITOR")
def create_folder(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Folder.objects.create(name=name, created_by=request.user)
            messages.success(request, "Folder created.")
        else:
            messages.error(request, "Folder name cannot be empty.")
    return redirect("folders_list")


@login_required
@role_required("ADMIN",)
def create_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category created.")
        else:
            messages.error(request, "Category name cannot be empty.")
    return redirect("folders_list")
