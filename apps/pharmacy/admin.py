from django.contrib import admin
from .models import Drug, DrugIssue, PrescriptionItem


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock_quantity", "low_stock_threshold", "expiration_date", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name",)


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ("patient", "drug", "quantity", "status", "total_price", "prescribed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("patient__first_name", "patient__last_name", "drug__name")


@admin.register(DrugIssue)
class DrugIssueAdmin(admin.ModelAdmin):
    list_display = ("prescription_item", "issued_by", "received_by_name", "issued_at")
    search_fields = ("prescription_item__patient__first_name", "prescription_item__drug__name")