import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from apps.accounts.models import Role
from apps.patients.models import Patient


class WaitingRoomEntry(models.Model):
    class Priority(models.IntegerChoices):
        EMERGENCY = 1, "Emergency"
        APPOINTMENT = 2, "Appointment"
        NORMAL = 3, "Normal"

    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        IN_CONSULTATION = "IN_CONSULTATION", "In Consultation"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="waiting_entries")
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.WAITING)
    is_active = models.BooleanField(default=True)

    assigned_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_waiting_entries",
        limit_choices_to={"role": Role.DOCTOR},
    )

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="waiting_entries_added",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["priority", "created_at"]

    def clean(self):
        if self.patient.is_deceased:
            raise ValidationError("A patient marked as deceased cannot be added to the waiting room.")

        duplicate_exists = WaitingRoomEntry.objects.filter(
            patient=self.patient,
            is_active=True,
        ).exclude(pk=self.pk).exists()

        if duplicate_exists:
            raise ValidationError("This patient is already in the waiting room.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.full_name} - {self.get_priority_display()}"