from django.contrib import admin

from .models import HospitalSetting


@admin.register(HospitalSetting)
class HospitalSettingAdmin(admin.ModelAdmin):
    list_display = (
        "hospital_name",
        "short_name",
        "hospital_phone",
        "hospital_email",
        "currency_symbol",
        "timezone_label",
        "updated_at",
    )

    def has_add_permission(self, request):
        return not HospitalSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False