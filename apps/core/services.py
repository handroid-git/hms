from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.admissions.models import Admission
from apps.billing.models import Billing
from apps.consultations.models import Consultation
from apps.patients.models import PatientRecord

from .models import HospitalSetting, RetentionExecutionLog


@transaction.atomic
def run_retention_archival(performed_by=None):
    hospital_settings = HospitalSetting.get_solo()
    retention_days = hospital_settings.record_retention_days
    cutoff = timezone.now() - timedelta(days=retention_days)

    consultations_to_archive = Consultation.objects.filter(
        is_archived=False,
        status__in=[
            Consultation.Status.COMPLETED,
            Consultation.Status.REFERRED,
            Consultation.Status.CANCELLED,
        ],
        updated_at__lt=cutoff,
    )

    admissions_to_archive = Admission.objects.filter(
        is_archived=False,
        status=Admission.Status.DISCHARGED,
        discharged_at__isnull=False,
        discharged_at__lt=cutoff,
    )

    patient_records_to_archive = PatientRecord.objects.filter(
        is_archived=False,
        updated_at__lt=cutoff,
    )

    billings_to_archive = Billing.objects.filter(
        is_archived=False,
        updated_at__lt=cutoff,
    )

    consultations_count = consultations_to_archive.count()
    admissions_count = admissions_to_archive.count()
    patient_records_count = patient_records_to_archive.count()
    billings_count = billings_to_archive.count()

    if consultations_count:
        consultations_to_archive.update(
            is_archived=True,
            archived_at=timezone.now(),
        )

    if admissions_count:
        admissions_to_archive.update(
            is_archived=True,
            archived_at=timezone.now(),
        )

    if patient_records_count:
        patient_records_to_archive.update(
            is_archived=True,
            archived_at=timezone.now(),
        )

    if billings_count:
        billings_to_archive.update(
            is_archived=True,
            archived_at=timezone.now(),
        )

    execution_log = RetentionExecutionLog.objects.create(
        retention_days_used=retention_days,
        consultations_archived=consultations_count,
        admissions_archived=admissions_count,
        patient_records_archived=patient_records_count,
        billings_archived=billings_count,
        status=RetentionExecutionLog.Status.COMPLETED,
        performed_by=performed_by,
        notes=f"Archival cutoff applied for records older than {retention_days} days.",
    )

    return execution_log