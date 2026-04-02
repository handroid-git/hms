from django.db import transaction
from django.utils import timezone
from apps.patients.models import Patient
from .models import Admission


@transaction.atomic
def create_admission_from_consultation(consultation, admitted_by, reason_for_admission="", ward="", bed_number="", surgery_performed=False, surgery_notes="", further_lab_tests="", visits_during_admission="", admission_extra_costs=0):
    active_admission = consultation.patient.admissions.filter(
        consultation=consultation,
        status__in=[Admission.Status.ACTIVE, Admission.Status.DISCHARGE_PENDING_NURSE],
    ).first()
    if active_admission:
        return active_admission

    admission = Admission.objects.create(
        patient=consultation.patient,
        consultation=consultation,
        reason_for_admission=reason_for_admission,
        ward=ward,
        bed_number=bed_number,
        surgery_performed=surgery_performed,
        surgery_notes=surgery_notes,
        further_lab_tests=further_lab_tests,
        visits_during_admission=visits_during_admission,
        admission_extra_costs=admission_extra_costs,
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
def doctor_mark_discharge_pending(admission, discharged_by, discharge_summary=""):
    admission.status = Admission.Status.DISCHARGE_PENDING_NURSE
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
    return admission


@transaction.atomic
def nurse_confirm_discharge(admission, nurse_user, nurse_note=""):
    admission.status = Admission.Status.DISCHARGED
    admission.nurse_discharge_confirmed_by = nurse_user
    admission.nurse_discharge_note = nurse_note
    admission.save(
        update_fields=[
            "status",
            "nurse_discharge_confirmed_by",
            "nurse_discharge_note",
            "updated_at",
        ]
    )

    patient = admission.patient
    patient.admission_status = Patient.Status.DISCHARGED
    patient.discharged_at = admission.discharged_at or timezone.now()
    patient.updated_by = nurse_user
    patient.save(update_fields=["admission_status", "discharged_at", "updated_by"])

    return admission