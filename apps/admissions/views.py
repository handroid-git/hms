from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import Role
from apps.consultations.models import Consultation
from .forms import (
    AdmissionCreateForm,
    AdmissionDischargeForm,
    InpatientNoteForm,
    MedicationAdministrationForm,
)
from .models import Admission, InpatientNote, MedicationAdministration
from .services import create_admission_from_consultation, discharge_admission


@login_required
def admission_list(request):
    admissions = Admission.objects.select_related("patient", "admitted_by").order_by("-admitted_at")
    active_admissions = admissions.filter(status=Admission.Status.ACTIVE)
    discharged_admissions = admissions.filter(status=Admission.Status.DISCHARGED)[:20]

    return render(
        request,
        "admissions/admission_list.html",
        {
            "active_admissions": active_admissions,
            "discharged_admissions": discharged_admissions,
        },
    )


@login_required
def admission_detail(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related("patient", "admitted_by", "discharged_by"),
        pk=pk,
    )

    notes = admission.notes.select_related("created_by").order_by("-created_at")
    medication_logs = admission.medication_administrations.select_related("administered_by").order_by("-administered_at")

    note_form = InpatientNoteForm()
    medication_form = MedicationAdministrationForm()
    discharge_form = AdmissionDischargeForm(instance=admission)

    return render(
        request,
        "admissions/admission_detail.html",
        {
            "admission": admission,
            "notes": notes,
            "medication_logs": medication_logs,
            "note_form": note_form,
            "medication_form": medication_form,
            "discharge_form": discharge_form,
        },
    )


@login_required
def admission_create_from_consultation_view(request, consultation_pk):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    consultation = get_object_or_404(
        Consultation.objects.select_related("patient"),
        pk=consultation_pk,
    )

    if request.method == "POST":
        form = AdmissionCreateForm(request.POST)
        if form.is_valid():
            admission = create_admission_from_consultation(
                consultation=consultation,
                admitted_by=request.user,
                reason_for_admission=form.cleaned_data["reason_for_admission"],
                ward=form.cleaned_data["ward"],
                bed_number=form.cleaned_data["bed_number"],
            )
            messages.success(request, "Patient admitted successfully.")
            return redirect("admission_detail", pk=admission.pk)
    else:
        form = AdmissionCreateForm()

    return render(
        request,
        "admissions/admission_form.html",
        {
            "form": form,
            "consultation": consultation,
            "title": "Admit Patient",
        },
    )


@login_required
def inpatient_note_create_view(request, admission_pk, note_type):
    admission = get_object_or_404(Admission, pk=admission_pk, status=Admission.Status.ACTIVE)

    if note_type == "doctor" and request.user.role not in [Role.DOCTOR, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    if note_type == "nurse" and request.user.role not in [Role.NURSE, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = InpatientNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.admission = admission
            note.created_by = request.user
            note.note_type = (
                InpatientNote.NoteType.DOCTOR if note_type == "doctor" else InpatientNote.NoteType.NURSE
            )
            note.save()
            messages.success(request, "Inpatient note added successfully.")
    return redirect("admission_detail", pk=admission.pk)


@login_required
def medication_administration_create_view(request, admission_pk):
    if request.user.role not in [Role.NURSE, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    admission = get_object_or_404(Admission, pk=admission_pk, status=Admission.Status.ACTIVE)

    if request.method == "POST":
        form = MedicationAdministrationForm(request.POST)
        if form.is_valid():
            administration = form.save(commit=False)
            administration.admission = admission
            administration.administered_by = request.user
            administration.save()
            messages.success(request, "Medication administration recorded successfully.")
    return redirect("admission_detail", pk=admission.pk)


@login_required
def discharge_admission_view(request, admission_pk):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    admission = get_object_or_404(Admission, pk=admission_pk, status=Admission.Status.ACTIVE)

    if request.method == "POST":
        form = AdmissionDischargeForm(request.POST, instance=admission)
        if form.is_valid():
            discharge_admission(
                admission=admission,
                discharged_by=request.user,
                discharge_summary=form.cleaned_data["discharge_summary"],
            )
            messages.success(request, "Patient discharged successfully.")
    return redirect("admission_detail", pk=admission.pk)