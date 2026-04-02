from django.db import transaction
from django.utils import timezone
from apps.patients.models import Patient
from .models import Admission


@transaction.atomic
def create_admission_from_consultation(consultation, admitted_by, reason_for_admission="", ward="", bed_number=""):
    active_admission = consultation.patient.admissions.filter(status=Admission.Status.ACTIVE).first()
    if active_admission:
        return active_admission

    admission = Admission.objects.create(
        patient=consultation.patient,
        consultation=consultation,
        reason_for_admission=reason_for_admission,
        ward=ward,
        bed_number=bed_number,
        admitted_by=admitted_by,
    )

    patient = consultation.patient
    patient.admission_status = Patient.Status.ADMITTED
    if not patient.admitted_at:
        patient.admitted_at = admission.admitted_at
    patient.updated_by = admitted_by
    patient.save(update_fields=["admission_status", "admitted_at", "updated_by"])

    return admission


@transaction.atomic
def discharge_admission(admission, discharged_by, discharge_summary=""):
    admission.status = Admission.Status.DISCHARGED
    admission.discharged_by = discharged_by
    admission.discharged_at = timezone.now()
    admission.discharge_summary = discharge_summary
    admission.save(
        update_fields=[
            "status",
            "discharged_by",
            "discharged_at",
            "discharge_summary",
            "updated_at",
        ]
    )

    patient = admission.patient
    patient.admission_status = Patient.Status.DISCHARGED
    patient.discharged_at = admission.discharged_at
    patient.updated_by = discharged_by
    patient.save(update_fields=["admission_status", "discharged_at", "updated_by"])

    return admission