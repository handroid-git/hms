import uuid
from django.conf import settings
from django.db import models


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ADMITTED = "ADMITTED", "Admitted"
        DISCHARGED = "DISCHARGED", "Discharged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    next_of_kin = models.CharField(max_length=255, blank=True)
    next_of_kin_phone = models.CharField(max_length=20, blank=True)

    admission_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCHARGED,
    )
    given_birth = models.BooleanField(default=False)
    is_deceased = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="patients_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.hospital_number} - {self.full_name}"


class PatientRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records")

    blood_pressure = models.CharField(max_length=20, blank=True)
    pulse = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    diagnosis = models.TextField(blank=True)
    medication = models.TextField(blank=True)
    laboratory_tests = models.TextField(blank=True)

    admitted = models.BooleanField(default=False)
    discharged = models.BooleanField(default=False)
    died = models.BooleanField(default=False)
    given_birth = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="patient_records_created",
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_records_edited",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def created_by_stamp(self):
        if self.created_by:
            return f"{self.created_by.get_full_name() or self.created_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    @property
    def edited_by_stamp(self):
        if self.edited_by:
            return f"{self.edited_by.get_full_name() or self.edited_by.username} | {self.updated_at:%Y-%m-%d %H:%M}"
        return "Not edited"

    def __str__(self):
        return f"Record - {self.patient.full_name}"