from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from apps.notifications.services import notify_pharmacists_payment_ready

from .models import Billing, BillingExtraItem, PaymentTransaction


def auto_archive_old_bills():
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    old_bills = Billing.objects.filter(
        is_archived=False,
        created_at__lt=cutoff,
    )
    for bill in old_bills:
        bill.is_archived = True
        bill.archived_at = timezone.now()
        bill.save(update_fields=["is_archived", "archived_at", "updated_at"])


def get_patient_outstanding_balance(patient):
    outstanding = Billing.objects.filter(
        patient=patient,
        is_archived=False,
        balance__gt=Decimal("0.00"),
    ).aggregate(total=models.Sum("balance"))
    return outstanding["total"] or Decimal("0.00")


@transaction.atomic
def update_billing_adjustments(billing, handled_by, consultation_fee, e_card_fee, other_charges, discount):
    if billing.is_archived and not billing.can_edit_archived_amounts:
        raise ValueError("Archived fully paid bills cannot be edited.")

    billing.consultation_fee = consultation_fee
    billing.e_card_fee = e_card_fee
    billing.other_charges = other_charges
    billing.discount = discount
    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()
    return billing


@transaction.atomic
def add_billing_extra_item(billing, handled_by, title, price):
    if billing.is_archived and not billing.can_edit_archived_amounts:
        raise ValueError("Archived fully paid bills cannot be edited.")

    BillingExtraItem.objects.create(
        billing=billing,
        title=title,
        price=price,
        created_by=handled_by,
        updated_by=handled_by,
    )
    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()
    return billing


@transaction.atomic
def update_billing_extra_item(extra_item, handled_by, title, price):
    billing = extra_item.billing

    if billing.is_archived and not billing.can_edit_archived_amounts:
        raise ValueError("Archived fully paid bills cannot be edited.")

    extra_item.title = title
    extra_item.price = price
    extra_item.updated_by = handled_by
    extra_item.save()

    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()
    return extra_item


@transaction.atomic
def receive_payment(billing, handled_by, amount, payment_type, notes=""):
    if billing.is_archived and not billing.can_edit_archived_amounts:
        raise ValueError("Archived fully paid bills cannot receive new payments.")

    PaymentTransaction.objects.create(
        billing=billing,
        amount=amount,
        payment_type=payment_type,
        notes=notes,
        received_by=handled_by,
    )

    billing.amount_paid += amount
    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()

    if billing.consultation:
        for prescription_item in billing.consultation.prescription_items.all():
            notify_pharmacists_payment_ready(prescription_item)

    return billing


@transaction.atomic
def archive_bill(billing, handled_by):
    billing.is_archived = True
    billing.archived_at = timezone.now()
    billing.handled_by = handled_by
    billing.save(update_fields=["is_archived", "archived_at", "handled_by", "updated_at"])
    return billing


@transaction.atomic
def update_billing_note(billing, handled_by, internal_note):
    billing.internal_note = internal_note
    billing.handled_by = handled_by
    billing.save(update_fields=["internal_note", "handled_by", "updated_at"])
    return billing