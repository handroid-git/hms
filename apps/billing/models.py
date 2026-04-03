import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.patients.models import Patient
from apps.consultations.models import Consultation


class Billing(models.Model):
    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PART_PAYMENT = "PART_PAYMENT", "Part Payment"
        PAID_FULL = "PAID_FULL", "Paid Full"
        DEPOSIT = "DEPOSIT", "Deposit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="billings",
    )
    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name="billing",
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="billings_created",
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billings_handled",
    )

    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    lab_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    prescription_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    medication_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    brought_forward_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    internal_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate_total(self):
        extras_total = sum((item.price for item in self.extra_items.all()), Decimal("0.00"))

        self.total_amount = (
            self.consultation_fee
            + self.lab_total
            + self.prescription_total
            + self.medication_total
            + self.other_charges
            + self.brought_forward_balance
            + extras_total
            - self.discount
        )
        if self.total_amount < Decimal("0.00"):
            self.total_amount = Decimal("0.00")

        self.balance = self.total_amount - self.amount_paid
        if self.balance < Decimal("0.00"):
            self.balance = Decimal("0.00")

        if self.amount_paid <= Decimal("0.00"):
            self.payment_status = self.PaymentStatus.UNPAID
        elif self.amount_paid >= self.total_amount and self.total_amount > Decimal("0.00"):
            self.payment_status = self.PaymentStatus.PAID_FULL
        elif self.amount_paid < self.total_amount:
            last_payment = self.payments.order_by("-created_at").first()
            if last_payment and last_payment.payment_type == PaymentTransaction.PaymentType.DEPOSIT:
                self.payment_status = self.PaymentStatus.DEPOSIT
            else:
                self.payment_status = self.PaymentStatus.PART_PAYMENT

        return self.total_amount

    @property
    def handled_by_stamp(self):
        if self.handled_by:
            return f"{self.handled_by.get_full_name() or self.handled_by.username} | {self.updated_at:%Y-%m-%d %H:%M}"
        return "Not yet handled"

    @property
    def can_edit_archived_amounts(self):
        if not self.is_archived:
            return True
        return self.payment_status in [self.PaymentStatus.UNPAID, self.PaymentStatus.PART_PAYMENT, self.PaymentStatus.DEPOSIT]

    def archive(self, user=None):
        self.is_archived = True
        self.archived_at = timezone.now()
        if user:
            self.handled_by = user
        self.save(update_fields=["is_archived", "archived_at", "handled_by", "updated_at"])

    def __str__(self):
        return f"Billing - {self.patient.full_name}"


class BillingExtraItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing = models.ForeignKey(
        Billing,
        on_delete=models.CASCADE,
        related_name="extra_items",
    )
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="billing_extra_items_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.billing.patient.full_name}"


class PaymentTransaction(models.Model):
    class PaymentType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        PART_PAYMENT = "PART_PAYMENT", "Part Payment"
        FULL_PAYMENT = "FULL_PAYMENT", "Full Payment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing = models.ForeignKey(
        Billing,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
    )
    notes = models.TextField(blank=True)

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments_received",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def received_by_stamp(self):
        if self.received_by:
            return f"{self.received_by.get_full_name() or self.received_by.username} | {self.created_at:%Y-%m-%d %H:%M}"
        return "Unknown"

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.billing.patient.full_name}"