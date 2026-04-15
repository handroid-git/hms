import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Drug(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    expiration_date = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_expired(self):
        return bool(self.expiration_date and self.expiration_date < timezone.localdate())

    @property
    def is_near_expiry(self):
        if not self.expiration_date:
            return False
        today = timezone.localdate()
        return today <= self.expiration_date <= (today + timezone.timedelta(days=30))

    @property
    def stock_status_label(self):
        if self.is_expired:
            return "Expired"
        if self.stock_quantity == 0:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"

    def __str__(self):
        return self.name


class PrescriptionItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        AWAITING_PAYMENT = "AWAITING_PAYMENT", "Awaiting Payment"
        READY_TO_ISSUE = "READY_TO_ISSUE", "Ready To Issue"
        ISSUED = "ISSUED", "Issued"
        CANCELLED = "CANCELLED", "Cancelled"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="prescription_items",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="prescription_items",
    )
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name="prescription_items",
    )

    quantity = models.PositiveIntegerField(default=1)
    dosage = models.CharField(max_length=255, blank=True)
    frequency = models.CharField(max_length=255, blank=True)
    route = models.CharField(max_length=255, blank=True)
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    instructions = models.TextField(blank=True)

    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AWAITING_PAYMENT,
    )

    prescribed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="drugs_prescribed",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    unavailable_note = models.TextField(blank=True)

    def recalculate_total(self):
        self.total_price = self.unit_price * self.quantity
        return self.total_price

    @property
    def prescription_summary(self):
        parts = []
        if self.dosage:
            parts.append(self.dosage)
        if self.frequency:
            parts.append(self.frequency)
        if self.route:
            parts.append(self.route)
        if self.duration_days:
            parts.append(f"{self.duration_days} day(s)")
        return " | ".join(parts) if parts else "-"

    def __str__(self):
        return f"{self.patient.full_name} - {self.drug.name}"


class DrugIssue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription_item = models.OneToOneField(
        PrescriptionItem,
        on_delete=models.CASCADE,
        related_name="issue_record",
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="drugs_issued",
    )
    received_by_name = models.CharField(max_length=255, blank=True)
    received_by_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    @property
    def issued_by_stamp(self):
        if self.issued_by:
            return f"{self.issued_by.get_full_name() or self.issued_by.username} | {self.issued_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"Issue - {self.prescription_item.patient.full_name} - {self.prescription_item.drug.name}"


class DrugRestock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name="restocks",
    )
    quantity_added = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    supplier_name = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=255, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    restocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drug_restocks_created",
    )
    restocked_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.unit_cost * self.quantity_added

    def __str__(self):
        return f"Restock - {self.drug.name} (+{self.quantity_added})"


class DrugStockMovement(models.Model):
    class MovementType(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        ISSUE = "ISSUE", "Issue"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drug = models.ForeignKey(
        Drug,
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
        related_name="drug_stock_movements",
    )
    prescription_item = models.ForeignKey(
        PrescriptionItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    restock_record = models.ForeignKey(
        DrugRestock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.drug.name} - {self.get_movement_type_display()} ({self.quantity})"