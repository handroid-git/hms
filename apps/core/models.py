from django.conf import settings
from django.db import models


class HospitalSetting(models.Model):
    hospital_name = models.CharField(max_length=255, default="Hospital Management System")
    short_name = models.CharField(max_length=50, default="HMS")
    hospital_address = models.TextField(blank=True)
    hospital_phone = models.CharField(max_length=50, blank=True)
    hospital_email = models.EmailField(blank=True)
    hospital_website = models.URLField(blank=True)
    hospital_motto = models.CharField(max_length=255, blank=True)
    hospital_logo = models.ImageField(upload_to="hospital/", blank=True, null=True)

    currency_symbol = models.CharField(max_length=10, default="₦")
    timezone_label = models.CharField(max_length=100, default="Africa/Lagos")
    default_e_card_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    record_retention_days = models.PositiveIntegerField(default=3650)

    backup_instructions = models.TextField(
        blank=True,
        help_text="Internal instructions for backup/export operations.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hospital Setting"
        verbose_name_plural = "Hospital Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.hospital_name


class BackupOperationLog(models.Model):
    class OperationType(models.TextChoices):
        BACKUP = "BACKUP", "Backup"
        RESTORE = "RESTORE", "Restore"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    class FileType(models.TextChoices):
        DATABASE = "DATABASE", "Database"
        MEDIA = "MEDIA", "Media"
        XLSX = "XLSX", "XLSX"
        PDF = "PDF", "PDF"
        JSON = "JSON", "JSON"
        OTHER = "OTHER", "Other"

    id = models.BigAutoField(primary_key=True)
    operation_type = models.CharField(
        max_length=20,
        choices=OperationType.choices,
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.DATABASE,
    )
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="backup_operations_performed",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Backup Operation Log"
        verbose_name_plural = "Backup Operation Logs"

    @property
    def performed_by_stamp(self):
        if self.performed_by:
            return f"{self.performed_by.get_full_name() or self.performed_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.title}"


class RetentionExecutionLog(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.BigAutoField(primary_key=True)
    retention_days_used = models.PositiveIntegerField(default=3650)
    consultations_archived = models.PositiveIntegerField(default=0)
    admissions_archived = models.PositiveIntegerField(default=0)
    patient_records_archived = models.PositiveIntegerField(default=0)
    billings_archived = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retention_runs_performed",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Retention Execution Log"
        verbose_name_plural = "Retention Execution Logs"

    @property
    def total_archived(self):
        return (
            self.consultations_archived
            + self.admissions_archived
            + self.patient_records_archived
            + self.billings_archived
        )

    @property
    def performed_by_stamp(self):
        if self.performed_by:
            return f"{self.performed_by.get_full_name() or self.performed_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "System"

    def __str__(self):
        return f"Retention Run - {self.created_at:%Y-%m-%d %H:%M}"