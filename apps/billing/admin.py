from django.contrib import admin
from .models import Billing, PaymentTransaction


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "payment_status",
        "total_amount",
        "amount_paid",
        "balance",
        "created_at",
    )
    list_filter = ("payment_status",)
    search_fields = ("patient__first_name", "patient__last_name", "patient__hospital_number")
    inlines = [PaymentTransactionInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("billing", "amount", "payment_type", "received_by", "created_at")
    list_filter = ("payment_type",)
    search_fields = ("billing__patient__first_name", "billing__patient__last_name")