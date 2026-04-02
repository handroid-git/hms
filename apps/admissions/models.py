import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Admission(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DISCHARGED = "DISCHARGED", "Discharged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="admissions",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    reason_for_admission = models.TextField(blank=True)
    ward = models.CharField(max_length=100, blank=True)
    bed_number = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admissions_created",
    )
    discharged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions_discharged",
    )

    admitted_at = models.DateTimeField(default=timezone.now)
    discharged_at = models.DateTimeField(null=True, blank=True)
    discharge_summary = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def days_admitted(self):
        end_time = self.discharged_at or timezone.now()
        return (end_time.date() - self.admitted_at.date()).days + 1

    @property
    def admitted_by_stamp(self):
        if self.admitted_by:
            return f"{self.admitted_by.get_full_name() or self.admitted_by.username} | {self.admitted_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    @property
    def discharged_by_stamp(self):
        if self.discharged_by and self.discharged_at:
            return f"{self.discharged_by.get_full_name() or self.discharged_by.username} | {self.discharged_at:%Y-%m-%d %H:%M}"
        return "Not discharged"

    def __str__(self):
        return f"{self.patient.full_name} - {self.get_status_display()}"


class InpatientNote(models.Model):
    class NoteType(models.TextChoices):
        DOCTOR = "DOCTOR", "Doctor Note"
        NURSE = "NURSE", "Nurse Note"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    note_type = models.CharField(
        max_length=20,
        choices=NoteType.choices,
    )
    note = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inpatient_notes_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_by_stamp(self):
        if self.created_by:
            return f"{self.created_by.get_full_name() or self.created_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"{self.get_note_type_display()} - {self.admission.patient.full_name}"


class MedicationAdministration(models.Model):
    class Route(models.TextChoices):
        ORAL = "ORAL", "Oral"
        IV = "IV", "IV"
        IM = "IM", "IM"
        TOPICAL = "TOPICAL", "Topical"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="medication_administrations",
    )
    prescription_item = models.ForeignKey(
        "pharmacy.PrescriptionItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administrations",
    )

    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    route = models.CharField(
        max_length=20,
        choices=Route.choices,
        default=Route.ORAL,
    )
    administration_notes = models.TextField(blank=True)

    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="medications_administered",
    )
    administered_at = models.DateTimeField(default=timezone.now)

    @property
    def administered_by_stamp(self):
        if self.administered_by:
            return f"{self.administered_by.get_full_name() or self.administered_by.username} | {self.administered_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"{self.medication_name} - {self.admission.patient.full_name}"