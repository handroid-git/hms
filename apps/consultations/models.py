import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.patients.models import Patient
from apps.waiting_room.models import WaitingRoomEntry


class Consultation(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        REFERRED = "REFERRED", "Referred"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="consultations",
    )
    waiting_room_entry = models.OneToOneField(
        WaitingRoomEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultation",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="consultations_handled",
    )

    complaint = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)
    medication = models.TextField(blank=True)
    laboratory_tests = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    admitted = models.BooleanField(default=False)
    discharged = models.BooleanField(default=False)
    died = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)

    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    consulted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.medication and not self.admitted:
            raise ValidationError(
                {"medication": "Medication can only be added after the patient is marked as admitted."}
            )

    @property
    def consulted_by_stamp(self):
        if self.doctor:
            return f"{self.doctor.get_full_name() or self.doctor.username} | {self.consulted_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    @property
    def is_ongoing(self):
        return self.status == self.Status.IN_PROGRESS and not self.complete

    def __str__(self):
        return f"{self.patient.full_name} - {self.get_status_display()}"