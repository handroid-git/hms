from django.contrib import admin
from .models import LabRequest, LabRequestItem, LabResultAttachment, LabTest


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_available", "stock_quantity", "low_stock_threshold")
    list_filter = ("is_available",)
    search_fields = ("name",)


class LabResultAttachmentInline(admin.TabularInline):
    model = LabResultAttachment
    extra = 0


class LabRequestItemInline(admin.TabularInline):
    model = LabRequestItem
    extra = 0


@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "consultation", "status", "requested_by", "assigned_to", "created_at", "ready_at")
    list_filter = ("status",)
    search_fields = ("patient__first_name", "patient__last_name")
    inlines = [LabRequestItemInline]


@admin.register(LabRequestItem)
class LabRequestItemAdmin(admin.ModelAdmin):
    list_display = ("lab_request", "lab_test", "status", "price", "uploaded_by", "doctor_reviewed_by")
    list_filter = ("status",)
    inlines = [LabResultAttachmentInline]


@admin.register(LabResultAttachment)
class LabResultAttachmentAdmin(admin.ModelAdmin):
    list_display = ("lab_request_item", "uploaded_by", "uploaded_at")