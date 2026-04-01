from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
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

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "records": records,
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