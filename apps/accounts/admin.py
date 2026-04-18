from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.action(description="Approve selected staff accounts")
def approve_users(modeladmin, request, queryset):
    for user in queryset:
        user.approve(request.user)


@admin.action(description="Reject selected staff accounts")
def reject_users(modeladmin, request, queryset):
    for user in queryset:
        user.reject(request.user)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "employee_id",
        "doctor_consultation_fee",
        "is_available_for_appointments",
        "verification_status",
        "is_verified_staff",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "role",
        "is_available_for_appointments",
        "verification_status",
        "is_verified_staff",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("username", "email", "employee_id", "first_name", "last_name")

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
                    "is_available_for_appointments",
                    "doctor_consultation_fee",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "is_verified_staff",
                    "verified_by",
                    "verified_at",
                )
            },
        ),
    )

    actions = [approve_users, reject_users]