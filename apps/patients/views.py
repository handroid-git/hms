from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import Role
from .forms import PatientForm
from .models import Patient


@login_required
def patient_list(request):
    query = request.GET.get("q", "").strip()

    patients = Patient.objects.all().order_by("-created_at")

    if query:
        patients = patients.filter(
            Q(hospital_number__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone_number__icontains=query)
        )

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients,
            "query": query,
        },
    )


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    records = patient.records.select_related("created_by", "edited_by", "consultation").order_by("-created_at")
    billing_history = None

    if request.user.role == Role.ACCOUNTANT or request.user.is_superuser:
        billing_history = patient.billings.select_related("consultation", "handled_by").order_by("-created_at")

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "records": records,
            "billing_history": billing_history,
        },
    )


@login_required
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.updated_by = request.user
            patient.save()
            messages.success(request, "Patient created successfully.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm()

    return render(request, "patients/patient_form.html", {"form": form, "title": "Create Patient"})


@login_required
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.updated_by = request.user
            patient.save()
            messages.success(request, "Patient updated successfully.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)

    return render(request, "patients/patient_form.html", {"form": form, "title": "Update Patient"})


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if not (request.user.role == Role.ADMIN or request.user.is_superuser):
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        patient_name = patient.full_name
        patient.delete()
        messages.success(request, f"Patient '{patient_name}' was deleted successfully.")
        return redirect("patient_list")

    return render(
        request,
        "patients/patient_confirm_delete.html",
        {
            "patient": patient,
        },
    )