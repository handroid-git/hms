from django.contrib import admin
from .models import Consultation


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "status", "consulted_at", "complete")
    list_filter = ("status", "complete", "doctor")
    search_fields = ("patient__first_name", "patient__last_name", "doctor__username")