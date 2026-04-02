from django.contrib import admin
from .models import Admission, InpatientNote, MedicationAdministration


class InpatientNoteInline(admin.TabularInline):
    model = InpatientNote
    extra = 0


class MedicationAdministrationInline(admin.TabularInline):
    model = MedicationAdministration
    extra = 0


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("patient", "status", "ward", "bed_number", "admitted_at", "discharged_at")
    list_filter = ("status", "ward")
    search_fields = ("patient__first_name", "patient__last_name", "patient__hospital_number")
    inlines = [InpatientNoteInline, MedicationAdministrationInline]


@admin.register(InpatientNote)
class InpatientNoteAdmin(admin.ModelAdmin):
    list_display = ("admission", "note_type", "created_by", "created_at")
    list_filter = ("note_type",)
    search_fields = ("admission__patient__first_name", "admission__patient__last_name")


@admin.register(MedicationAdministration)
class MedicationAdministrationAdmin(admin.ModelAdmin):
    list_display = ("admission", "medication_name", "route", "administered_by", "administered_at")
    list_filter = ("route",)
    search_fields = ("admission__patient__first_name", "admission__patient__last_name", "medication_name")