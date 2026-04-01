from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.accounts.models import Role
from apps.consultations.models import Consultation
from apps.laboratory.models import LabRequest
from apps.patients.models import Patient
from apps.waiting_room.models import WaitingRoomEntry
from apps.waiting_room.services import waiting_room_is_overloaded


@login_required
def nurse_dashboard(request):
    patients_created_count = Patient.objects.filter(created_by=request.user).count()
    active_waiting_count = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).count()

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

    context = {
        "active_waiting_count": active_waiting_count,
        "in_progress_consultations": in_progress_consultations,
        "completed_count": completed_count,
        "total_bill_generated": total_bill_generated,
        "next_patients": next_patients,
        "doctor_lab_reviews": doctor_lab_reviews,
        "is_overloaded": waiting_room_is_overloaded(),
    }
    return render(request, "dashboards/doctor_dashboard.html", context)