import uuid
from django.conf import settings
from django.db import models
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

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="waiting_entries_added",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["priority", "created_at"]

    def __str__(self):
        return f"{self.patient.full_name} - {self.get_priority_display()}"