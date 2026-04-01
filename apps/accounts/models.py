import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    DOCTOR = "DOCTOR", "Doctor"
    NURSE = "NURSE", "Nurse"
    ACCOUNTANT = "ACCOUNTANT", "Accountant"
    LAB_TECHNICIAN = "LAB_TECHNICIAN", "Lab Technician"
    PHARMACIST = "PHARMACIST", "Pharmacist"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=30, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    shift_start = models.TimeField(blank=True, null=True)
    shift_end = models.TimeField(blank=True, null=True)
    shift_days = models.JSONField(default=list, blank=True)

    is_available_for_appointments = models.BooleanField(default=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    is_verified_staff = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_users",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def approve(self, approved_by):
        self.is_active = True
        self.is_verified_staff = True
        self.verification_status = VerificationStatus.APPROVED
        self.verified_by = approved_by
        self.verified_at = timezone.now()
        self.save(
            update_fields=[
                "is_active",
                "is_verified_staff",
                "verification_status",
                "verified_by",
                "verified_at",
            ]
        )

    def reject(self, rejected_by=None):
        self.is_active = False
        self.is_verified_staff = False
        self.verification_status = VerificationStatus.REJECTED
        self.verified_by = rejected_by
        self.verified_at = timezone.now()
        self.save(
            update_fields=[
                "is_active",
                "is_verified_staff",
                "verification_status",
                "verified_by",
                "verified_at",
            ]
        )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = Role.ADMIN
            self.is_active = True
            self.is_verified_staff = True
            self.verification_status = VerificationStatus.APPROVED
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"