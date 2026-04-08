from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from .models import PayrollRecord, StaffSalaryStructure


@transaction.atomic
def generate_payroll_for_period(year, month, generated_by):
    staff_members = User.objects.filter(
        is_active=True,
        is_verified_staff=True,
    ).order_by("first_name", "last_name", "username")

    created_or_updated = []

    for staff in staff_members:
        structure = getattr(staff, "salary_structure", None)
        base_salary = structure.base_salary if structure and structure.is_active else 0

        payroll, _ = PayrollRecord.objects.get_or_create(
            staff=staff,
            year=year,
            month=month,
            defaults={
                "base_salary": base_salary,
                "generated_by": generated_by,
                "status": PayrollRecord.Status.GENERATED,
            },
        )

        if payroll.status != PayrollRecord.Status.PAID:
            payroll.base_salary = base_salary
            if payroll.status == PayrollRecord.Status.DRAFT:
                payroll.status = PayrollRecord.Status.GENERATED
            payroll.generated_by = generated_by
            payroll.recalculate_net_pay()
            payroll.save()

        created_or_updated.append(payroll)

    return created_or_updated


@transaction.atomic
def update_payroll_record(payroll, bonus, deduction, accountant_note, updated_by):
    if payroll.status == PayrollRecord.Status.PAID:
        raise ValueError("A paid payroll record cannot be edited.")

    payroll.bonus = bonus
    payroll.deduction = deduction
    payroll.accountant_note = accountant_note
    payroll.generated_by = updated_by
    payroll.recalculate_net_pay()
    payroll.save()
    return payroll


@transaction.atomic
def mark_payroll_paid(payroll, paid_by):
    payroll.recalculate_net_pay()
    payroll.status = PayrollRecord.Status.PAID
    payroll.paid_by = paid_by
    payroll.paid_at = timezone.now()
    payroll.save()
    return payroll