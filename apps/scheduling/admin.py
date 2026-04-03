from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "reassigned_to",
        "appointment_date",
        "appointment_time",
        "status",
    )
    list_filter = ("status", "appointment_date")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "patient__hospital_number",
        "doctor__first_name",
        "doctor__last_name",
    )