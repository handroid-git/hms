from django.contrib import admin
from .models import Billing


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "consultation",
        "payment_status",
        "total_amount",
        "amount_paid",
        "created_at",
    )
    list_filter = ("payment_status",)
    search_fields = ("patient__first_name", "patient__last_name")