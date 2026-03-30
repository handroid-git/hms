from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PatientForm, PatientRecordForm
from .models import Patient


@login_required
def patient_list(request):
    patients = Patient.objects.all().order_by("-created_at")
    return render(request, "patients/patient_list.html", {"patients": patients})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    records = patient.records.all().order_by("-created_at")
    return render(
        request,
        "patients/patient_detail.html",
        {"patient": patient, "records": records},
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
def patient_record_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)

    if request.method == "POST":
        form = PatientRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.created_by = request.user
            record.save()
            messages.success(request, "Patient record added successfully.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientRecordForm()

    return render(
        request,
        "patients/patient_record_form.html",
        {"form": form, "patient": patient},
    )