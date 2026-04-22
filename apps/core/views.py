from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from apps.accounts.models import Role
from apps.admissions.models import Admission
from apps.billing.models import Billing
from apps.consultations.models import Consultation
from apps.patients.models import Patient, PatientRecord

from .forms import BackupOperationLogForm, HospitalSettingForm
from .models import BackupOperationLog, HospitalSetting, RetentionExecutionLog
from .services import run_retention_archival


def home(request):
    return render(request, "core/home.html")


@login_required
def hospital_settings_view(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    hospital_settings = HospitalSetting.get_solo()

    if request.method == "POST":
        form = HospitalSettingForm(request.POST, request.FILES, instance=hospital_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Hospital operational settings updated successfully.")
            return redirect("hospital_settings")
    else:
        form = HospitalSettingForm(instance=hospital_settings)

    return render(
        request,
        "core/hospital_settings.html",
        {
            "form": form,
            "hospital_settings": hospital_settings,
        },
    )


@login_required
def backup_center_view(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    hospital_settings = HospitalSetting.get_solo()

    if request.method == "POST":
        log_form = BackupOperationLogForm(request.POST)
        if log_form.is_valid():
            backup_log = log_form.save(commit=False)
            backup_log.performed_by = request.user
            backup_log.save()
            messages.success(request, "Backup or restore operation logged successfully.")
            return redirect("backup_center")
    else:
        log_form = BackupOperationLogForm()

    total_patients = Patient.objects.count()
    total_consultations = Consultation.objects.count()
    total_billings = Billing.objects.count()
    total_admissions = Admission.objects.count()
    total_active_admissions = Admission.objects.filter(
        status__in=[Admission.Status.ACTIVE, Admission.Status.DISCHARGE_PENDING_NURSE]
    ).count()
    total_archived_bills = Billing.objects.filter(is_archived=True).count()
    total_outstanding_balance = (
        Billing.objects.filter(balance__gt=0, is_archived=False).aggregate(total=Sum("balance")).get("total") or 0
    )

    latest_patient = Patient.objects.order_by("-created_at").first()
    latest_consultation = Consultation.objects.order_by("-consulted_at").first()
    latest_billing = Billing.objects.order_by("-created_at").first()
    latest_admission = Admission.objects.order_by("-admitted_at").first()

    recent_operations = BackupOperationLog.objects.select_related("performed_by")[:10]

    context = {
        "hospital_settings": hospital_settings,
        "log_form": log_form,
        "recent_operations": recent_operations,
        "total_patients": total_patients,
        "total_consultations": total_consultations,
        "total_billings": total_billings,
        "total_admissions": total_admissions,
        "total_active_admissions": total_active_admissions,
        "total_archived_bills": total_archived_bills,
        "total_outstanding_balance": total_outstanding_balance,
        "latest_patient": latest_patient,
        "latest_consultation": latest_consultation,
        "latest_billing": latest_billing,
        "latest_admission": latest_admission,
    }
    return render(request, "core/backup_center.html", context)


@login_required
def retention_center_view(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    hospital_settings = HospitalSetting.get_solo()

    if request.method == "POST":
        execution_log = run_retention_archival(performed_by=request.user)
        messages.success(
            request,
            f"Retention run completed successfully. Archived {execution_log.total_archived} records.",
        )
        return redirect("retention_center")

    archived_consultations = Consultation.objects.filter(is_archived=True).count()
    archived_admissions = Admission.objects.filter(is_archived=True).count()
    archived_patient_records = PatientRecord.objects.filter(is_archived=True).count()
    archived_billings = Billing.objects.filter(is_archived=True).count()

    recent_runs = RetentionExecutionLog.objects.select_related("performed_by")[:10]

    context = {
        "hospital_settings": hospital_settings,
        "archived_consultations": archived_consultations,
        "archived_admissions": archived_admissions,
        "archived_patient_records": archived_patient_records,
        "archived_billings": archived_billings,
        "recent_runs": recent_runs,
    }
    return render(request, "core/retention_center.html", context)