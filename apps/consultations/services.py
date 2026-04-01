from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.billing.models import Billing
from apps.consultations.models import Consultation
from apps.patients.models import Patient, PatientRecord
from apps.waiting_room.models import WaitingRoomEntry

DEFAULT_CONSULTATION_FEE = Decimal("5000.00")
DEFAULT_LAB_TEST_PRICE = Decimal("2000.00")
DEFAULT_PRESCRIPTION_PRICE = Decimal("1500.00")
DEFAULT_MEDICATION_PRICE = Decimal("2500.00")


def get_next_waiting_patient(doctor):
    emergency_entry = (
        WaitingRoomEntry.objects.filter(
            is_active=True,
            status=WaitingRoomEntry.Status.WAITING,
            priority=WaitingRoomEntry.Priority.EMERGENCY,
        )
        .select_related("patient", "added_by", "assigned_doctor")
        .order_by("created_at")
        .first()
    )
    if emergency_entry:
        return emergency_entry

    assigned_appointment = (
        WaitingRoomEntry.objects.filter(
            is_active=True,
            status=WaitingRoomEntry.Status.WAITING,
            priority=WaitingRoomEntry.Priority.APPOINTMENT,
            assigned_doctor=doctor,
        )
        .select_related("patient", "added_by", "assigned_doctor")
        .order_by("created_at")
        .first()
    )
    if assigned_appointment:
        return assigned_appointment

    unavailable_assigned_appointment = (
        WaitingRoomEntry.objects.filter(
            is_active=True,
            status=WaitingRoomEntry.Status.WAITING,
            priority=WaitingRoomEntry.Priority.APPOINTMENT,
            assigned_doctor__isnull=False,
            assigned_doctor__is_available_for_appointments=False,
        )
        .exclude(assigned_doctor=doctor)
        .select_related("patient", "added_by", "assigned_doctor")
        .order_by("created_at")
        .first()
    )
    if unavailable_assigned_appointment:
        return unavailable_assigned_appointment

    normal_entry = (
        WaitingRoomEntry.objects.filter(
            is_active=True,
            status=WaitingRoomEntry.Status.WAITING,
            priority=WaitingRoomEntry.Priority.NORMAL,
        )
        .select_related("patient", "added_by", "assigned_doctor")
        .order_by("created_at")
        .first()
    )
    if normal_entry:
        return normal_entry

    unassigned_appointment = (
        WaitingRoomEntry.objects.filter(
            is_active=True,
            status=WaitingRoomEntry.Status.WAITING,
            priority=WaitingRoomEntry.Priority.APPOINTMENT,
            assigned_doctor__isnull=True,
        )
        .select_related("patient", "added_by", "assigned_doctor")
        .order_by("created_at")
        .first()
    )
    return unassigned_appointment


@transaction.atomic
def start_consultation_for_next_patient(doctor):
    entry = get_next_waiting_patient(doctor)
    if not entry:
        return None

    entry.status = WaitingRoomEntry.Status.IN_CONSULTATION
    entry.save(update_fields=["status"])

    consultation = Consultation.objects.create(
        patient=entry.patient,
        waiting_room_entry=entry,
        doctor=doctor,
        consultation_fee=DEFAULT_CONSULTATION_FEE,
        status=Consultation.Status.IN_PROGRESS,
    )

    billing = Billing.objects.create(
        patient=entry.patient,
        consultation=consultation,
        created_by=doctor,
        consultation_fee=DEFAULT_CONSULTATION_FEE,
    )
    billing.recalculate_total()
    billing.save(update_fields=["total_amount"])

    return consultation


@transaction.atomic
def update_consultation_billing(consultation):
    billing = consultation.billing

    lab_total = Decimal("0.00")
    prescription_total = Decimal("0.00")
    medication_total = Decimal("0.00")

    if consultation.laboratory_tests.strip():
        lab_total = DEFAULT_LAB_TEST_PRICE

    if consultation.prescriptions.strip():
        prescription_total = DEFAULT_PRESCRIPTION_PRICE

    if consultation.medication.strip():
        medication_total = DEFAULT_MEDICATION_PRICE

    billing.lab_total = lab_total
    billing.prescription_total = prescription_total
    billing.medication_total = medication_total
    billing.consultation_fee = consultation.consultation_fee
    billing.recalculate_total()
    billing.save()

    patient = consultation.patient

    if consultation.admitted:
        patient.admission_status = Patient.Status.ADMITTED
        if not patient.admitted_at:
            patient.admitted_at = timezone.now()

    if consultation.discharged:
        patient.admission_status = Patient.Status.DISCHARGED
        if not patient.discharged_at:
            patient.discharged_at = timezone.now()

    if consultation.died:
        patient.is_deceased = True

    patient.updated_by = consultation.doctor
    patient.save(
        update_fields=[
            "admission_status",
            "admitted_at",
            "discharged_at",
            "is_deceased",
            "updated_by",
        ]
    )


@transaction.atomic
def complete_consultation(consultation):
    consultation.complete = True
    consultation.status = Consultation.Status.COMPLETED
    consultation.save(update_fields=["complete", "status"])

    triage = None
    if consultation.waiting_room_entry and hasattr(consultation.waiting_room_entry, "triage_record"):
        triage = consultation.waiting_room_entry.triage_record

    record, _ = PatientRecord.objects.get_or_create(
        consultation=consultation,
        defaults={
            "patient": consultation.patient,
            "record_type": PatientRecord.RecordType.CONSULTATION_SESSION,
            "created_by": consultation.doctor,
        },
    )

    record.patient = consultation.patient
    record.record_type = PatientRecord.RecordType.CONSULTATION_SESSION

    if triage:
        record.blood_pressure = triage.blood_pressure
        record.pulse = triage.pulse
        record.weight = triage.weight
        record.body_temperature = triage.body_temperature
        record.notes = "\n\n".join(
            [text for text in [triage.notes, consultation.notes] if text]
        )
    else:
        record.notes = consultation.notes

    record.diagnosis = consultation.diagnosis
    record.prescriptions = consultation.prescriptions
    record.medication = consultation.medication
    record.laboratory_tests = consultation.laboratory_tests
    record.admitted = consultation.admitted
    record.discharged = consultation.discharged
    record.died = consultation.died
    record.edited_by = consultation.doctor

    if not record.created_by:
        record.created_by = consultation.doctor

    record.save()

    if triage:
        triage.is_consumed = True
        triage.consumed_at = timezone.now()
        triage.save(update_fields=["is_consumed", "consumed_at"])

    if consultation.waiting_room_entry:
        consultation.waiting_room_entry.is_active = False
        consultation.waiting_room_entry.status = WaitingRoomEntry.Status.COMPLETED
        consultation.waiting_room_entry.save(update_fields=["is_active", "status"])