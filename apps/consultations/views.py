from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Role
from apps.laboratory.services import sync_lab_requests_for_consultation
from apps.pharmacy.models import Drug
from apps.pharmacy.services import (
    sync_prescriptions_for_consultation,
    update_prescription_details_from_post,
)

from .forms import ConsultationUpdateForm
from .models import Consultation
from .services import (
    complete_consultation,
    start_consultation_for_next_patient,
    update_consultation_billing,
)


def _can_access_doctor_consultation_area(user):
    return user.role in [Role.DOCTOR, Role.ADMIN] or user.is_superuser


def _build_prescription_rows(consultation, request=None):
    existing_items = {
        str(item.drug_id): item
        for item in consultation.prescription_items.select_related("drug").all()
    }

    if request and request.method == "POST":
        selected_drug_ids = set(request.POST.getlist("selected_drugs"))
    else:
        selected_drug_ids = set(existing_items.keys())

    rows = []
    for drug in Drug.objects.filter(is_available=True).order_by("name"):
        existing = existing_items.get(str(drug.pk))
        rows.append(
            {
                "drug": drug,
                "selected": str(drug.pk) in selected_drug_ids,
                "quantity": request.POST.get(
                    f"prescription_quantity_{drug.pk}",
                    getattr(existing, "quantity", 1),
                )
                if request and request.method == "POST"
                else getattr(existing, "quantity", 1),
                "dosage": request.POST.get(
                    f"prescription_dosage_{drug.pk}",
                    getattr(existing, "dosage", ""),
                )
                if request and request.method == "POST"
                else getattr(existing, "dosage", ""),
                "frequency": request.POST.get(
                    f"prescription_frequency_{drug.pk}",
                    getattr(existing, "frequency", ""),
                )
                if request and request.method == "POST"
                else getattr(existing, "frequency", ""),
                "route": request.POST.get(
                    f"prescription_route_{drug.pk}",
                    getattr(existing, "route", ""),
                )
                if request and request.method == "POST"
                else getattr(existing, "route", ""),
                "duration_days": request.POST.get(
                    f"prescription_duration_days_{drug.pk}",
                    getattr(existing, "duration_days", ""),
                )
                if request and request.method == "POST"
                else (getattr(existing, "duration_days", "") or ""),
                "instructions": request.POST.get(
                    f"prescription_instructions_{drug.pk}",
                    getattr(existing, "instructions", ""),
                )
                if request and request.method == "POST"
                else getattr(existing, "instructions", ""),
            }
        )
    return rows


@login_required
def doctor_consultation_start(request):
    if not _can_access_doctor_consultation_area(request.user):
        messages.error(request, "Only doctors or admins can start consultations.")
        return redirect("dashboard_redirect")

    consultation = start_consultation_for_next_patient(request.user)

    if consultation is None:
        messages.warning(request, "No patients are currently waiting.")
        return redirect("doctor_dashboard" if request.user.role == Role.DOCTOR else "admin_dashboard")

    messages.success(request, "Consultation started successfully.")
    return redirect("consultation_detail", pk=consultation.pk)


@login_required
def doctor_ongoing_consultations(request):
    if not _can_access_doctor_consultation_area(request.user):
        messages.error(request, "Only doctors or admins can access ongoing consultations.")
        return redirect("dashboard_redirect")

    consultations = Consultation.objects.select_related(
        "patient",
        "waiting_room_entry",
        "doctor",
    ).filter(
        status=Consultation.Status.IN_PROGRESS,
        complete=False,
    )

    if request.user.role == Role.DOCTOR and not request.user.is_superuser:
        consultations = consultations.filter(doctor=request.user)

    consultations = consultations.order_by("-updated_at")

    return render(
        request,
        "consultations/ongoing_consultations.html",
        {
            "consultations": consultations,
        },
    )


@login_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(
        Consultation.objects.select_related(
            "patient",
            "doctor",
            "waiting_room_entry",
        ).prefetch_related(
            "prescription_items__drug",
            "lab_requests__items__lab_test",
            "lab_requests__items__attachments",
        ),
        pk=pk,
    )

    if not _can_access_doctor_consultation_area(request.user):
        messages.error(request, "Only doctors or admins can access consultations.")
        return redirect("dashboard_redirect")

    if (
        request.user.role == Role.DOCTOR
        and consultation.doctor_id
        and consultation.doctor_id != request.user.id
        and not request.user.is_superuser
    ):
        messages.error(request, "You can only access consultations assigned to you.")
        return redirect("doctor_dashboard")

    triage_record = None
    if consultation.waiting_room_entry and hasattr(consultation.waiting_room_entry, "triage_record"):
        triage_record = consultation.waiting_room_entry.triage_record

    lab_request = consultation.lab_requests.prefetch_related(
        "items__lab_test",
        "items__attachments",
    ).first()
    prescription_items = consultation.prescription_items.select_related("drug").all()

    if request.method == "POST":
        form = ConsultationUpdateForm(request.POST, instance=consultation)
        if form.is_valid():
            try:
                with transaction.atomic():
                    consultation = form.save()

                    selected_tests = form.cleaned_data.get("selected_lab_tests")
                    selected_drugs = form.cleaned_data.get("selected_drugs")

                    sync_lab_requests_for_consultation(consultation, selected_tests, request.user)
                    sync_prescriptions_for_consultation(consultation, selected_drugs, request.user)
                    update_prescription_details_from_post(consultation, request.POST)

                    update_consultation_billing(consultation)

                messages.success(request, "Consultation updated successfully.")
                return redirect("consultation_detail", pk=consultation.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = ConsultationUpdateForm(instance=consultation)

    return render(
        request,
        "consultations/consultation_detail.html",
        {
            "consultation": consultation,
            "form": form,
            "triage_record": triage_record,
            "lab_request": lab_request,
            "prescription_items": prescription_items,
            "prescription_rows": _build_prescription_rows(consultation, request),
        },
    )


@login_required
def consultation_complete_view(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if not _can_access_doctor_consultation_area(request.user):
        messages.error(request, "Only doctors or admins can complete consultations.")
        return redirect("dashboard_redirect")

    if (
        request.user.role == Role.DOCTOR
        and consultation.doctor_id
        and consultation.doctor_id != request.user.id
        and not request.user.is_superuser
    ):
        messages.error(request, "You can only complete consultations assigned to you.")
        return redirect("doctor_dashboard")

    if consultation.patient.admission_status == "ADMITTED":
        messages.error(request, "An admitted patient cannot be marked complete. Discharge the patient first.")
        return redirect("consultation_detail", pk=consultation.pk)

    complete_consultation(consultation)
    messages.success(request, "Consultation marked as complete and added to medical history.")

    if request.user.role == Role.ADMIN or request.user.is_superuser:
        return redirect("doctor_ongoing_consultations")
    return redirect("doctor_dashboard")