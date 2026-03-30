import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    DOCTOR = "DOCTOR", "Doctor"
    NURSE = "NURSE", "Nurse"
    ACCOUNTANT = "ACCOUNTANT", "Accountant"
    LAB_TECHNICIAN = "LAB_TECHNICIAN", "Lab Technician"
    PHARMACIST = "PHARMACIST", "Pharmacist"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=30, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    shift_start = models.TimeField(blank=True, null=True)
    shift_end = models.TimeField(blank=True, null=True)
    shift_days = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"