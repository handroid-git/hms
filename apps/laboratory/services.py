from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.notifications.services import (
    notify_doctor_lab_ready,
    notify_doctor_lab_unavailable,
    notify_lab_rejected,
)
from .models import LabRequest, LabRequestItem, LabResultAttachment


@transaction.atomic
def sync_lab_requests_for_consultation(consultation, selected_tests, requested_by):
    existing_request = consultation.lab_requests.first()

    if existing_request:
        lab_request = existing_request
        lab_request.requested_by = requested_by
        lab_request.save(update_fields=["requested_by", "updated_at"])
    else:
        lab_request = LabRequest.objects.create(
            consultation=consultation,
            patient=consultation.patient,
            requested_by=requested_by,
            status=LabRequest.Status.PENDING,
        )

    selected_test_ids = set(test.pk for test in selected_tests)
    existing_items = {
        item.lab_test_id: item
        for item in lab_request.items.select_related("lab_test").all()
    }

    for test in selected_tests:
        if test.pk not in existing_items:
            LabRequestItem.objects.create(
                lab_request=lab_request,
                lab_test=test,
                price=test.price,
                status=LabRequestItem.Status.PENDING,
            )

    for lab_test_id, item in existing_items.items():
        if lab_test_id not in selected_test_ids and item.status != LabRequestItem.Status.ACCEPTED:
            item.attachments.all().delete()
            item.delete()

    update_lab_request_status(lab_request)
    update_consultation_lab_summary(consultation)
    update_billing_lab_total(consultation)

    return lab_request


def update_consultation_lab_summary(consultation):
    lab_request = consultation.lab_requests.first()
    if not lab_request:
        consultation.laboratory_tests = ""
        consultation.save(update_fields=["laboratory_tests"])
        return

    names = [
        item.lab_test.name
        for item in lab_request.items.exclude(status=LabRequestItem.Status.UNAVAILABLE).select_related("lab_test")
    ]
    consultation.laboratory_tests = ", ".join(names)
    consultation.save(update_fields=["laboratory_tests"])


def update_billing_lab_total(consultation):
    billing = consultation.billing
    lab_request = consultation.lab_requests.first()

    if not lab_request:
        billing.lab_total = Decimal("0.00")
    else:
        total = sum(
            (
                item.price
                for item in lab_request.items.exclude(status=LabRequestItem.Status.UNAVAILABLE)
            ),
            Decimal("0.00"),
        )
        billing.lab_total = total

    billing.recalculate_total()
    billing.save()


def update_lab_request_status(lab_request):
    items = list(lab_request.items.all())

    previous_status = lab_request.status

    if not items:
        lab_request.status = LabRequest.Status.PENDING
        lab_request.ready_at = None
    elif any(item.status == LabRequestItem.Status.REJECTED for item in items):
        lab_request.status = LabRequest.Status.REJECTED
        lab_request.ready_at = None
    elif any(item.status == LabRequestItem.Status.PENDING for item in items):
        lab_request.status = LabRequest.Status.PENDING
        lab_request.ready_at = None
    elif any(item.status == LabRequestItem.Status.IN_PROGRESS for item in items):
        lab_request.status = LabRequest.Status.IN_PROGRESS
        lab_request.ready_at = None
    elif any(item.status == LabRequestItem.Status.READY for item in items):
        lab_request.status = LabRequest.Status.READY
        if not lab_request.ready_at:
            lab_request.ready_at = timezone.now()
    elif all(item.status == LabRequestItem.Status.UNAVAILABLE for item in items):
        lab_request.status = LabRequest.Status.UNAVAILABLE
        lab_request.ready_at = None
    elif all(item.status in [LabRequestItem.Status.ACCEPTED, LabRequestItem.Status.UNAVAILABLE] for item in items):
        if any(item.status == LabRequestItem.Status.ACCEPTED for item in items):
            lab_request.status = LabRequest.Status.ACCEPTED
        else:
            lab_request.status = LabRequest.Status.UNAVAILABLE
    else:
        lab_request.status = LabRequest.Status.IN_PROGRESS
        lab_request.ready_at = None

    lab_request.save(update_fields=["status", "ready_at", "updated_at"])

    if lab_request.status == LabRequest.Status.READY and previous_status != LabRequest.Status.READY:
        notify_doctor_lab_ready(lab_request)


@transaction.atomic
def technician_update_result_item(item, form, files, user):
    item = form.save(commit=False)

    if item.status == LabRequestItem.Status.READY:
        item.uploaded_by = user
        item.uploaded_at = timezone.now()
        item.unavailable_note = ""
    elif item.status == LabRequestItem.Status.UNAVAILABLE:
        item.result_text = ""
    else:
        item.unavailable_note = ""

    item.save()

    uploaded_files = form.cleaned_data.get("attachments", [])
    for uploaded_file in uploaded_files:
        LabResultAttachment.objects.create(
            lab_request_item=item,
            file=uploaded_file,
            uploaded_by=user,
        )

    update_lab_request_status(item.lab_request)
    update_billing_lab_total(item.lab_request.consultation)
    update_consultation_lab_summary(item.lab_request.consultation)

    if item.status == LabRequestItem.Status.UNAVAILABLE:
        notify_doctor_lab_unavailable(item.lab_request, item)

    return item


@transaction.atomic
def doctor_accept_result(item, doctor):
    item.status = LabRequestItem.Status.ACCEPTED
    item.doctor_reviewed_by = doctor
    item.doctor_reviewed_at = timezone.now()
    item.save(update_fields=["status", "doctor_reviewed_by", "doctor_reviewed_at"])

    update_lab_request_status(item.lab_request)
    update_billing_lab_total(item.lab_request.consultation)
    update_consultation_lab_summary(item.lab_request.consultation)


@transaction.atomic
def doctor_reject_result(item, doctor):
    item.status = LabRequestItem.Status.REJECTED
    item.doctor_reviewed_by = doctor
    item.doctor_reviewed_at = timezone.now()
    item.save(update_fields=["status", "doctor_reviewed_by", "doctor_reviewed_at"])

    update_lab_request_status(item.lab_request)
    update_billing_lab_total(item.lab_request.consultation)
    update_consultation_lab_summary(item.lab_request.consultation)
    notify_lab_rejected(item)