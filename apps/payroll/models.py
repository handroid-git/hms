import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class StaffSalaryStructure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_structure",
    )
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_structures_updated",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff} Salary Structure"


class PayrollRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        GENERATED = "GENERATED", "Generated"
        PAID = "PAID", "Paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )

    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()

    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    accountant_note = models.TextField(blank=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payrolls_generated",
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payrolls_paid",
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("staff", "year", "month")
        ordering = ["-year", "-month", "staff__first_name", "staff__last_name", "staff__username"]

    def recalculate_net_pay(self):
        self.net_pay = self.base_salary + self.bonus - self.deduction
        if self.net_pay < Decimal("0.00"):
            self.net_pay = Decimal("0.00")
        return self.net_pay

    @property
    def period_label(self):
        return f"{self.year}-{self.month:02d}"

    def __str__(self):
        return f"{self.staff} Payroll {self.period_label}"