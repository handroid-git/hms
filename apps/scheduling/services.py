from django.db import transaction
from django.utils import timezone
from apps.waiting_room.models import WaitingRoomEntry
from .models import Appointment


@transaction.atomic
def check_in_appointment(appointment, checked_in_by):
    appointment.status = Appointment.Status.CHECKED_IN
    appointment.checked_in_at = timezone.now()
    appointment.save(update_fields=["status", "checked_in_at", "updated_at"])

    assigned_doctor = appointment.assigned_doctor

    existing_entry = WaitingRoomEntry.objects.filter(
        patient=appointment.patient,
        is_active=True,
    ).first()

    if not existing_entry:
        WaitingRoomEntry.objects.create(
            patient=appointment.patient,
            priority=WaitingRoomEntry.Priority.APPOINTMENT,
            status=WaitingRoomEntry.Status.WAITING,
            is_active=True,
            assigned_doctor=assigned_doctor,
            added_by=checked_in_by,
        )

    return appointment


@transaction.atomic
def complete_appointment(appointment):
    appointment.status = Appointment.Status.COMPLETED
    appointment.completed_at = timezone.now()
    appointment.save(update_fields=["status", "completed_at", "updated_at"])
    return appointment


@transaction.atomic
def cancel_appointment(appointment):
    appointment.status = Appointment.Status.CANCELLED
    appointment.cancelled_at = timezone.now()
    appointment.save(update_fields=["status", "cancelled_at", "updated_at"])
    return appointment


@transaction.atomic
def reassign_appointment_if_needed(appointment):
    doctor = appointment.doctor
    if doctor and getattr(doctor, "is_available_for_appointments", True):
        return appointment

    available_doctor = (
        type(doctor).objects.filter(
            role=doctor.role if doctor else "DOCTOR",
            is_active=True,
            is_verified_staff=True,
            is_available_for_appointments=True,
        )
        .exclude(pk=doctor.pk if doctor else None)
        .order_by("first_name", "last_name", "username")
        .first()
    )

    if available_doctor:
        appointment.reassigned_to = available_doctor
        appointment.status = Appointment.Status.REASSIGNED
        appointment.save(update_fields=["reassigned_to", "status", "updated_at"])

    return appointment