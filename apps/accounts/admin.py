from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "employee_id", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Hospital Info",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "profile_picture",
                    "employee_id",
                    "shift_start",
                    "shift_end",
                    "shift_days",
                )
            },
        ),
    )