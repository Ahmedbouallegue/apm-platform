from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "department",
        "is_staff",
        "is_active",
        "last_login",
    )
    list_filter = ("role", "is_staff", "is_active", "department")
    search_fields = ("username", "email", "first_name", "last_name", "department", "phone")
    ordering = ("username",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profil APM", {"fields": ("role", "phone", "department")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Profil APM", {"fields": ("role", "phone", "department", "email")}),
    )
