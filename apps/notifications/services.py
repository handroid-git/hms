from apps.accounts.models import Role, User
from .models import Notification, NotificationPreference


def get_or_create_notification_preference(user):
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    return preference


def get_general_unread_notifications_count(user):
    preference = get_or_create_notification_preference(user)

    notifications = user.notifications.filter(is_read=False)

    if not preference.include_chat_in_general_notifications:
        notifications = notifications.exclude(category=Notification.Category.CHAT)

    return notifications.count()


def create_notification(
    user,
    title,
    message,
    notification_type="INFO",
    link="",
    category=Notification.Category.WORKFLOW,
):
    if not user:
        return None

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        category=category,
        link=link,
    )


def notify_doctor_lab_ready(lab_request):
    doctor = getattr(lab_request.consultation, "doctor", None)
    if not doctor:
        return

    create_notification(
        user=doctor,
        title="Lab Result Ready",
        message=f"Lab results for {lab_request.patient.full_name} are ready for review.",
        notification_type="SUCCESS",
        link=f"/consultations/{lab_request.consultation.pk}/",
        category=Notification.Category.WORKFLOW,
    )


def notify_doctor_lab_unavailable(lab_request, item):
    doctor = getattr(lab_request.consultation, "doctor", None)
    if not doctor:
        return

    create_notification(
        user=doctor,
        title="Lab Test Unavailable",
        message=f"{item.lab_test.name} for {lab_request.patient.full_name} was marked unavailable.",
        notification_type="WARNING",
        link=f"/consultations/{lab_request.consultation.pk}/",
        category=Notification.Category.WORKFLOW,
    )


def notify_lab_rejected(item):
    technician = item.uploaded_by
    if not technician:
        return

    create_notification(
        user=technician,
        title="Lab Result Rejected",
        message=f"The result for {item.lab_test.name} on {item.lab_request.patient.full_name} was rejected by the doctor.",
        notification_type="ERROR",
        link=f"/laboratory/requests/{item.lab_request.pk}/",
        category=Notification.Category.WORKFLOW,
    )


def notify_pharmacists_payment_ready(prescription_item):
    pharmacists = User.objects.filter(
        role=Role.PHARMACIST,
        is_active=True,
        is_verified_staff=True,
    )

    for pharmacist in pharmacists:
        create_notification(
            user=pharmacist,
            title="Prescription Ready For Dispensing",
            message=f"Payment has been made for {prescription_item.patient.full_name}'s prescription: {prescription_item.drug.name}.",
            notification_type="SUCCESS",
            link=f"/pharmacy/prescriptions/{prescription_item.pk}/",
            category=Notification.Category.WORKFLOW,
        )


def notify_waiting_room_overload(users, count):
    for user in users:
        create_notification(
            user=user,
            title="Waiting Room Overload",
            message=f"The waiting room currently has {count} active patients.",
            notification_type="WARNING",
            link="/waiting-room/",
            category=Notification.Category.WORKFLOW,
        )


def notify_nurse_discharge_confirmation_needed(admission):
    nurses = User.objects.filter(
        role=Role.NURSE,
        is_active=True,
        is_verified_staff=True,
    )
    for nurse in nurses:
        create_notification(
            user=nurse,
            title="Discharge Confirmation Needed",
            message=f"{admission.patient.full_name} is waiting for nurse discharge confirmation.",
            notification_type="INFO",
            link=f"/admissions/{admission.pk}/",
            category=Notification.Category.WORKFLOW,
        )


def notify_doctor_discharge_confirmed(admission):
    doctor = admission.discharged_by
    if not doctor:
        return

    create_notification(
        user=doctor,
        title="Discharge Confirmed",
        message=f"Nurse discharge confirmation was completed for {admission.patient.full_name}.",
        notification_type="SUCCESS",
        link=f"/admissions/{admission.pk}/",
        category=Notification.Category.WORKFLOW,
    )