import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


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
    admitted_at = models.DateTimeField(blank=True, null=True)
    discharged_at = models.DateTimeField(blank=True, null=True)

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

    @property
    def admitted_days(self):
        if not self.admitted_at:
            return 0
        end_time = self.discharged_at or timezone.now()
        return (end_time.date() - self.admitted_at.date()).days + 1

    def __str__(self):
        return f"{self.hospital_number} - {self.full_name}"


class TriageRecord(models.Model):
    """
    Nurse vitals collected before the patient enters the waiting room.
    This is NOT permanent medical history by itself.
    It becomes part of the final session history after doctor completes consultation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="triage_records")
    waiting_room_entry = models.OneToOneField(
        "waiting_room.WaitingRoomEntry",
        on_delete=models.CASCADE,
        related_name="triage_record",
    )

    blood_pressure = models.CharField(max_length=20, blank=True)
    pulse = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="triage_records_created",
    )
    is_consumed = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_by_stamp(self):
        if self.created_by:
            return f"{self.created_by.get_full_name() or self.created_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"Triage - {self.patient.full_name}"


class PatientRecord(models.Model):
    class RecordType(models.TextChoices):
        CONSULTATION_SESSION = "CONSULTATION_SESSION", "Consultation Session"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records")
    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_record",
    )

    record_type = models.CharField(
        max_length=30,
        choices=RecordType.choices,
        default=RecordType.CONSULTATION_SESSION,
    )

    blood_pressure = models.CharField(max_length=20, blank=True)
    pulse = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    body_temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    diagnosis = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)
    medication = models.TextField(blank=True)
    laboratory_tests = models.TextField(blank=True)
    notes = models.TextField(blank=True)

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
        return f"{self.get_record_type_display()} - {self.patient.full_name}"