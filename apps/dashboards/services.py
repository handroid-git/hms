import calendar
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.admissions.models import Admission
from apps.billing.models import Billing
from apps.consultations.models import Consultation
from apps.laboratory.models import LabRequest, LabRequestItem, LabTest
from apps.patients.models import Patient
from apps.pharmacy.models import Drug, PrescriptionItem
from apps.waiting_room.models import WaitingRoomEntry


def doctor_dashboard_data(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    consultations = Consultation.objects.filter(doctor=user)

    total_consulted = consultations.count()
    consultations_today = consultations.filter(consulted_at__date=today).count()
    consultations_month = consultations.filter(consulted_at__date__gte=month_start).count()

    days_active = consultations.dates("consulted_at", "day").count()
    avg_per_day = round(total_consulted / days_active, 2) if days_active > 0 else 0

    total_bills = (
        Billing.objects.filter(consultation__doctor=user)
        .aggregate(total=Sum("total_amount"))
        .get("total")
        or Decimal("0.00")
    )

    admissions_count = Admission.objects.filter(
        consultation__doctor=user
    ).count()

    pending_lab_reviews = LabRequestItem.objects.filter(
        lab_request__consultation__doctor=user,
        status=LabRequestItem.Status.READY,
    ).count()

    return {
        "total_consulted": total_consulted,
        "consultations_today": consultations_today,
        "consultations_month": consultations_month,
        "avg_per_day": avg_per_day,
        "total_bills": total_bills,
        "admissions_count": admissions_count,
        "pending_lab_reviews": pending_lab_reviews,
    }


def nurse_dashboard_data(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    patients = Patient.objects.filter(created_by=user)
    waiting_entries = WaitingRoomEntry.objects.filter(added_by=user)

    total_patients_created = patients.count()
    patients_created_today = patients.filter(created_at__date=today).count()
    patients_created_month = patients.filter(created_at__date__gte=month_start).count()

    total_triaged = waiting_entries.count()
    triaged_today = waiting_entries.filter(created_at__date=today).count()

    # Only count patients who are still actually waiting in the queue.
    # Do not include patients already moved into consultation.
    active_waiting_room_count = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING,
    ).count()

    my_active_waiting_room_count = WaitingRoomEntry.objects.filter(
        added_by=user,
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING,
    ).count()

    discharge_pending_count = Admission.objects.filter(
        status=Admission.Status.DISCHARGE_PENDING_NURSE
    ).count()

    outstanding_patient_balances = (
        Billing.objects.filter(balance__gt=Decimal("0.00"), is_archived=False)
        .aggregate(total=Sum("balance"))
        .get("total")
        or Decimal("0.00")
    )

    return {
        "total_patients_created": total_patients_created,
        "patients_created_today": patients_created_today,
        "patients_created_month": patients_created_month,
        "total_triaged": total_triaged,
        "triaged_today": triaged_today,
        "active_waiting_room_count": active_waiting_room_count,
        "my_active_waiting_room_count": my_active_waiting_room_count,
        "discharge_pending_count": discharge_pending_count,
        "outstanding_patient_balances": outstanding_patient_balances,
        "shift_days": getattr(user, "shift_days", []),
        "shift_start": getattr(user, "shift_start", None),
        "shift_end": getattr(user, "shift_end", None),
    }


def accountant_dashboard_data(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    all_bills = Billing.objects.all()
    active_bills = all_bills.filter(is_archived=False)

    return {
        "total_bills_count": all_bills.count(),
        "active_bills_count": active_bills.count(),
        "archived_bills_count": all_bills.filter(is_archived=True).count(),
        "bills_today": all_bills.filter(created_at__date=today).count(),
        "total_billing_generated": all_bills.aggregate(total=Sum("total_amount")).get("total") or Decimal("0.00"),
        "billing_generated_today": all_bills.filter(created_at__date=today).aggregate(total=Sum("total_amount")).get("total") or Decimal("0.00"),
        "total_payments_received": all_bills.aggregate(total=Sum("amount_paid")).get("total") or Decimal("0.00"),
        "payments_received_today": all_bills.filter(updated_at__date=today).aggregate(total=Sum("amount_paid")).get("total") or Decimal("0.00"),
        "outstanding_balances": active_bills.filter(balance__gt=Decimal("0.00")).aggregate(total=Sum("balance")).get("total") or Decimal("0.00"),
        "unpaid_bills_count": active_bills.filter(payment_status=Billing.PaymentStatus.UNPAID).count(),
        "part_paid_bills_count": active_bills.filter(
            payment_status__in=[Billing.PaymentStatus.PART_PAYMENT, Billing.PaymentStatus.DEPOSIT]
        ).count(),
        "paid_full_today_count": active_bills.filter(
            payment_status=Billing.PaymentStatus.PAID_FULL,
            updated_at__date=today,
        ).count(),
        "monthly_generated": all_bills.filter(created_at__date__gte=month_start).aggregate(total=Sum("total_amount")).get("total") or Decimal("0.00"),
        "monthly_received": all_bills.filter(updated_at__date__gte=month_start).aggregate(total=Sum("amount_paid")).get("total") or Decimal("0.00"),
    }


def lab_dashboard_data(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    items = LabRequestItem.objects.all()

    completed_items = items.filter(
        status__in=[LabRequestItem.Status.READY, LabRequestItem.Status.ACCEPTED],
        uploaded_at__isnull=False,
    )

    return {
        "tests_today": completed_items.filter(uploaded_at__date=today).count(),
        "tests_month": completed_items.filter(uploaded_at__date__gte=month_start).count(),
        "tests_total": completed_items.count(),
        "pending_tests": items.filter(
            status__in=[LabRequestItem.Status.PENDING, LabRequestItem.Status.IN_PROGRESS]
        ).count(),
        "rejected_tests": items.filter(status=LabRequestItem.Status.REJECTED).count(),
        "unavailable_tests": items.filter(status=LabRequestItem.Status.UNAVAILABLE).count(),
        "available_tests": LabTest.objects.filter(is_available=True).count(),
    }


def pharmacy_dashboard_data(user):
    drugs = Drug.objects.all()

    return {
        "total_drugs": drugs.count(),
        "available_drugs": drugs.filter(stock_quantity__gt=0).count(),
        "low_stock": drugs.filter(stock_quantity__lte=10, stock_quantity__gt=0).count(),
        "out_of_stock": drugs.filter(stock_quantity=0).count(),
    }


def admin_dashboard_data(user):
    today = timezone.localdate()
    current_year = today.year

    verified_staff = User.objects.filter(is_verified_staff=True)
    pending_verification = User.objects.filter(is_active=False)

    total_staff = verified_staff.count()
    total_patients = Patient.objects.count()
    patients_today = Patient.objects.filter(created_at__date=today).count()
    active_waiting_room = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING,
    ).count()
    total_consultations = Consultation.objects.count()
    total_revenue = Billing.objects.aggregate(total=Sum("amount_paid")).get("total") or Decimal("0.00")

    total_admissions = Admission.objects.count()

    unpaid_bills_count = Billing.objects.filter(
        is_archived=False,
        payment_status=Billing.PaymentStatus.UNPAID,
    ).count()

    part_paid_bills_count = Billing.objects.filter(
        is_archived=False,
        payment_status__in=[
            Billing.PaymentStatus.PART_PAYMENT,
            Billing.PaymentStatus.DEPOSIT,
        ],
    ).count()

    paid_full_bills_count = Billing.objects.filter(
        is_archived=False,
        payment_status=Billing.PaymentStatus.PAID_FULL,
    ).count()

    pending_lab_count = LabRequestItem.objects.filter(
        status__in=[
            LabRequestItem.Status.PENDING,
            LabRequestItem.Status.IN_PROGRESS,
            LabRequestItem.Status.REJECTED,
        ]
    ).count()

    low_stock_drug_count = Drug.objects.filter(
        stock_quantity__lte=10,
        stock_quantity__gt=0,
    ).count()

    role_counts = {
        "admins": verified_staff.filter(role=Role.ADMIN).count(),
        "doctors": verified_staff.filter(role=Role.DOCTOR).count(),
        "nurses": verified_staff.filter(role=Role.NURSE).count(),
        "accountants": verified_staff.filter(role=Role.ACCOUNTANT).count(),
        "lab_technicians": verified_staff.filter(role=Role.LAB_TECHNICIAN).count(),
        "pharmacists": verified_staff.filter(role=Role.PHARMACIST).count(),
    }

    monthly_labels = [calendar.month_abbr[m] for m in range(1, 13)]
    monthly_patient_counts = []
    monthly_consultation_counts = []
    monthly_revenue_received = []

    for month in range(1, 13):
        patient_count = Patient.objects.filter(
            created_at__year=current_year,
            created_at__month=month,
        ).count()

        consultation_count = Consultation.objects.filter(
            consulted_at__year=current_year,
            consulted_at__month=month,
        ).count()

        revenue = (
            Billing.objects.filter(
                updated_at__year=current_year,
                updated_at__month=month,
            ).aggregate(total=Sum("amount_paid")).get("total")
            or Decimal("0.00")
        )

        monthly_patient_counts.append(patient_count)
        monthly_consultation_counts.append(consultation_count)
        monthly_revenue_received.append(float(revenue))

    workflow_distribution = {
        "waiting_room": active_waiting_room,
        "consultations": total_consultations,
        "admissions": total_admissions,
        "pending_lab": pending_lab_count,
    }

    billing_distribution = {
        "unpaid": unpaid_bills_count,
        "part_paid": part_paid_bills_count,
        "paid_full": paid_full_bills_count,
    }

    return {
        "total_staff": total_staff,
        "pending_verification": pending_verification.count(),
        "total_patients": total_patients,
        "patients_today": patients_today,
        "active_waiting_room": active_waiting_room,
        "total_consultations": total_consultations,
        "total_revenue": total_revenue,
        "total_admissions": total_admissions,
        "unpaid_bills_count": unpaid_bills_count,
        "part_paid_bills_count": part_paid_bills_count,
        "paid_full_bills_count": paid_full_bills_count,
        "pending_lab_count": pending_lab_count,
        "low_stock_drug_count": low_stock_drug_count,
        "role_counts": role_counts,
        "monthly_labels": monthly_labels,
        "monthly_patient_counts": monthly_patient_counts,
        "monthly_consultation_counts": monthly_consultation_counts,
        "monthly_revenue_received": monthly_revenue_received,
        "workflow_distribution": workflow_distribution,
        "billing_distribution": billing_distribution,
        "current_year": current_year,
    }


def lab_dashboard_workflow_context(user):
    active_requests = LabRequest.objects.filter(
        status__in=[
            LabRequest.Status.PENDING,
            LabRequest.Status.IN_PROGRESS,
            LabRequest.Status.REJECTED,
        ]
    ).select_related(
        "patient",
        "consultation",
        "consultation__billing",
    ).order_by("-updated_at")

    pending_items = LabRequestItem.objects.filter(
        status__in=[
            LabRequestItem.Status.PENDING,
            LabRequestItem.Status.IN_PROGRESS,
            LabRequestItem.Status.REJECTED,
        ]
    ).select_related(
        "lab_request",
        "lab_request__patient",
        "lab_request__consultation",
        "lab_request__consultation__doctor",
        "lab_test",
    ).order_by("-id")

    available_tests = LabTest.objects.order_by("name")
    low_stock_tests = [test for test in available_tests if test.is_low_stock]

    today = timezone.localdate()
    completed_today = LabRequestItem.objects.filter(
        uploaded_by=user,
        status=LabRequestItem.Status.ACCEPTED,
        doctor_reviewed_at__date=today,
    ).count()

    completed_all_time = LabRequestItem.objects.filter(
        uploaded_by=user,
        status=LabRequestItem.Status.ACCEPTED,
    ).count()

    return {
        "active_requests": active_requests,
        "pending_items": pending_items,
        "available_tests": available_tests[:10],
        "low_stock_tests": low_stock_tests,
        "completed_today": completed_today,
        "completed_all_time": completed_all_time,
    }


def pharmacy_dashboard_workflow_context(user):
    pending_items = PrescriptionItem.objects.filter(
        status__in=[
            PrescriptionItem.Status.AWAITING_PAYMENT,
            PrescriptionItem.Status.READY_TO_ISSUE,
            PrescriptionItem.Status.UNAVAILABLE,
        ]
    ).select_related("patient", "drug", "consultation").order_by("-updated_at")

    available_drugs = Drug.objects.order_by("name")
    low_stock_drugs = [drug for drug in available_drugs if drug.is_low_stock]
    expired_drugs = [drug for drug in available_drugs if drug.is_expired]

    today = timezone.localdate()
    issued_today = PrescriptionItem.objects.filter(
        status=PrescriptionItem.Status.ISSUED,
        issue_record__issued_by=user,
        issue_record__issued_at__date=today,
    ).count()

    issued_all_time = PrescriptionItem.objects.filter(
        status=PrescriptionItem.Status.ISSUED,
        issue_record__issued_by=user,
    ).count()

    return {
        "pending_items": pending_items,
        "low_stock_drugs": low_stock_drugs,
        "expired_drugs": expired_drugs,
        "issued_today": issued_today,
        "issued_all_time": issued_all_time,
    }