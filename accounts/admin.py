from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("DataNest Role", {"fields": ("role", "status")}),  # status = active/inactive flag
    )
    list_display = ("username", "email", "role", "is_staff", "status", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "status")

