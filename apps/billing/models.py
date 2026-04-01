import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
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
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate_total(self):
        self.total_amount = (
            self.consultation_fee
            + self.lab_total
            + self.prescription_total
            + self.medication_total
            + self.other_charges
            - self.discount
        )
        return self.total_amount

    def __str__(self):
        return f"Billing - {self.patient.full_name}"