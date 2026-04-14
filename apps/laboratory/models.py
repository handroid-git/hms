import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class LabTest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def stock_status_label(self):
        if self.stock_quantity == 0:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"

    def __str__(self):
        return self.name


class LabRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        READY = "READY", "Ready for Doctor Review"
        REJECTED = "REJECTED", "Rejected by Doctor"
        ACCEPTED = "ACCEPTED", "Accepted by Doctor"
        UNAVAILABLE = "UNAVAILABLE", "Not Available"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="lab_requests",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="lab_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lab_requests_created",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_requests_assigned",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ready_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lab Request - {self.patient.full_name}"


class LabRequestItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        READY = "READY", "Ready for Doctor Review"
        REJECTED = "REJECTED", "Rejected by Doctor"
        ACCEPTED = "ACCEPTED", "Accepted by Doctor"
        UNAVAILABLE = "UNAVAILABLE", "Not Available"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_request = models.ForeignKey(
        LabRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="request_items",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    result_text = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_results_uploaded",
    )
    uploaded_at = models.DateTimeField(null=True, blank=True)

    doctor_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_results_reviewed",
    )
    doctor_reviewed_at = models.DateTimeField(null=True, blank=True)

    unavailable_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.lab_test.name} - {self.lab_request.patient.full_name}"


class LabResultAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_request_item = models.ForeignKey(
        LabRequestItem,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="lab_results/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_result_attachments_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class LabTestRestock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="restocks",
    )
    quantity_added = models.PositiveIntegerField()
    supplier_name = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    restocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_test_restocks_created",
    )
    restocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Restock - {self.lab_test.name} (+{self.quantity_added})"


class LabStockMovement(models.Model):
    class MovementType(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        CONSUMPTION = "CONSUMPTION", "Consumption"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.IntegerField()
    previous_stock = models.PositiveIntegerField(default=0)
    new_stock = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_stock_movements",
    )
    lab_request_item = models.ForeignKey(
        LabRequestItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    restock_record = models.ForeignKey(
        LabTestRestock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lab_test.name} - {self.get_movement_type_display()} ({self.quantity})"