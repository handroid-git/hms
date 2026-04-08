from django.contrib import admin
from .models import PayrollRecord, StaffSalaryStructure


@admin.register(StaffSalaryStructure)
class StaffSalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("staff", "base_salary", "is_active", "effective_from", "updated_at")
    list_filter = ("is_active", "effective_from")
    search_fields = ("staff__username", "staff__first_name", "staff__last_name")


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ("staff", "year", "month", "net_pay", "status", "paid_at")
    list_filter = ("status", "year", "month")
    search_fields = ("staff__username", "staff__first_name", "staff__last_name")