from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from apps.accounts.models import Role
from apps.admissions.models import Admission
from apps.billing.models import Billing
from apps.consultations.models import Consultation
from apps.laboratory.models import LabRequest
from apps.patients.models import Patient
from apps.pharmacy.models import PrescriptionItem
from apps.waiting_room.models import WaitingRoomEntry
from apps.waiting_room.services import waiting_room_is_overloaded


@login_required
def nurse_dashboard(request):
    patients_created_count = Patient.objects.filter(created_by=request.user).count()
    active_waiting_count = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).count()

    admitted_patients = Admission.objects.filter(
        status=Admission.Status.ACTIVE
    ).select_related("patient").order_by("-admitted_at")[:10]

    recent_patients = Patient.objects.order_by("-created_at")[:5]
    recent_waiting_entries = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).select_related("patient").order_by("priority", "created_at")[:5]

    context = {
        "patients_created_count": patients_created_count,
        "active_waiting_count": active_waiting_count,
        "recent_patients": recent_patients,
        "recent_waiting_entries": recent_waiting_entries,
        "admitted_patients": admitted_patients,
        "is_overloaded": waiting_room_is_overloaded(),
    }
    return render(request, "dashboards/nurse_dashboard.html", context)


@login_required
def doctor_dashboard(request):
    if request.user.role != Role.DOCTOR:
        return render(request, "dashboards/access_denied.html", status=403)

    active_waiting_count = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING,
    ).count()

    in_progress_consultations = Consultation.objects.filter(
        doctor=request.user,
        status=Consultation.Status.IN_PROGRESS,
    ).select_related("patient").order_by("-consulted_at")

    completed_count = Consultation.objects.filter(
        doctor=request.user,
        status=Consultation.Status.COMPLETED,
    ).count()

    total_bill_generated = sum(
        c.billing.total_amount for c in Consultation.objects.filter(doctor=request.user).select_related("billing")
        if hasattr(c, "billing")
    )

    next_patients = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING,
    ).select_related("patient", "assigned_doctor").order_by("priority", "created_at")[:5]

    doctor_lab_reviews = LabRequest.objects.filter(
        consultation__doctor=request.user,
        consultation__status=Consultation.Status.IN_PROGRESS,
        status__in=[
            LabRequest.Status.READY,
            LabRequest.Status.ACCEPTED,
            LabRequest.Status.UNAVAILABLE,
        ],
    ).select_related("patient", "consultation").order_by("-updated_at")

    pending_prescriptions = PrescriptionItem.objects.filter(
        consultation__doctor=request.user,
        consultation__status=Consultation.Status.IN_PROGRESS,
        status__in=[
            PrescriptionItem.Status.AWAITING_PAYMENT,
            PrescriptionItem.Status.READY_TO_ISSUE,
            PrescriptionItem.Status.UNAVAILABLE,
        ],
    ).select_related("patient", "drug").order_by("-updated_at")[:10]

    active_admissions = Admission.objects.filter(
        status=Admission.Status.ACTIVE
    ).select_related("patient").order_by("-admitted_at")[:10]

    context = {
        "active_waiting_count": active_waiting_count,
        "in_progress_consultations": in_progress_consultations,
        "completed_count": completed_count,
        "total_bill_generated": total_bill_generated,
        "next_patients": next_patients,
        "doctor_lab_reviews": doctor_lab_reviews,
        "pending_prescriptions": pending_prescriptions,
        "active_admissions": active_admissions,
        "is_overloaded": waiting_room_is_overloaded(),
    }
    return render(request, "dashboards/doctor_dashboard.html", context)


@login_required
def accountant_dashboard(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    today = timezone.localdate()

    total_generated_today = (
        Billing.objects.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )
    total_paid_today = (
        Billing.objects.filter(updated_at__date=today).aggregate(total=Sum("amount_paid"))["total"]
        or 0
    )
    bills_today_count = Billing.objects.filter(created_at__date=today).count()
    all_time_processed = Billing.objects.exclude(handled_by__isnull=True).count()

    recent_bills = Billing.objects.select_related("patient").order_by("-updated_at")[:10]

    context = {
        "total_generated_today": total_generated_today,
        "total_paid_today": total_paid_today,
        "bills_today_count": bills_today_count,
        "all_time_processed": all_time_processed,
        "recent_bills": recent_bills,
    }
    return render(request, "dashboards/accountant_dashboard.html", context)