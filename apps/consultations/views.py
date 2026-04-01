from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import Role
from apps.laboratory.services import sync_lab_requests_for_consultation
from apps.pharmacy.services import sync_prescriptions_for_consultation
from .forms import ConsultationUpdateForm
from .models import Consultation
from .services import (
    complete_consultation,
    start_consultation_for_next_patient,
    update_consultation_billing,
)


@login_required
def doctor_consultation_start(request):
    if request.user.role != Role.DOCTOR:
        messages.error(request, "Only doctors can start consultations.")
        return redirect("dashboard_redirect")

    consultation = start_consultation_for_next_patient(request.user)

    if consultation is None:
        messages.warning(request, "No patients are currently waiting.")
        return redirect("doctor_dashboard")

    messages.success(request, "Consultation started successfully.")
    return redirect("consultation_detail", pk=consultation.pk)


@login_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(
        Consultation.objects.select_related("patient", "doctor", "billing", "waiting_room_entry"),
        pk=pk,
    )

    if request.user.role != Role.DOCTOR:
        messages.error(request, "Only doctors can access consultations.")
        return redirect("dashboard_redirect")

    triage_record = None
    if consultation.waiting_room_entry and hasattr(consultation.waiting_room_entry, "triage_record"):
        triage_record = consultation.waiting_room_entry.triage_record

    lab_request = consultation.lab_requests.prefetch_related("items__lab_test", "items__attachments").first()
    prescription_items = consultation.prescription_items.select_related("drug").all()

    if request.method == "POST":
        form = ConsultationUpdateForm(request.POST, instance=consultation)
        if form.is_valid():
            consultation = form.save()

            selected_tests = form.cleaned_data.get("selected_lab_tests")
            selected_drugs = form.cleaned_data.get("selected_drugs")

            sync_lab_requests_for_consultation(consultation, selected_tests, request.user)
            sync_prescriptions_for_consultation(consultation, selected_drugs, request.user)

            update_consultation_billing(consultation)
            messages.success(request, "Consultation updated successfully.")
            return redirect("consultation_detail", pk=consultation.pk)
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
        },
    )


@login_required
def consultation_complete_view(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)

    if request.user.role != Role.DOCTOR:
        messages.error(request, "Only doctors can complete consultations.")
        return redirect("dashboard_redirect")

    complete_consultation(consultation)
    messages.success(request, "Consultation marked as complete and added to medical history.")
    return redirect("doctor_dashboard")