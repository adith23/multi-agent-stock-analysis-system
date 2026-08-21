from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import User


@admin.register(User)
class PlatformUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Platform access", {"fields": ("role", "job_title")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Platform access", {"fields": ("email", "role", "job_title")}),
    )
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = UserAdmin.list_filter + ("role",)
