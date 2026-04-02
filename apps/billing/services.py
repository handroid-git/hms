from django.db import transaction
from .models import BillingExtraItem, PaymentTransaction


@transaction.atomic
def update_billing_adjustments(billing, handled_by, other_charges, discount):
    billing.other_charges = other_charges
    billing.discount = discount
    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()
    return billing


@transaction.atomic
def add_billing_extra_item(billing, handled_by, title, price):
    BillingExtraItem.objects.create(
        billing=billing,
        title=title,
        price=price,
        created_by=handled_by,
    )
    billing.handled_by = handled_by
    billing.recalculate_total()
    billing.save()
    return billing


@transaction.atomic
def receive_payment(billing, handled_by, amount, payment_type, notes=""):
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

    return billing


@transaction.atomic
def archive_paid_bill(billing, handled_by):
    if billing.payment_status != "PAID_FULL":
        raise ValueError("Only fully paid bills can be archived.")

    billing.is_archived = True
    billing.handled_by = handled_by
    billing.save(update_fields=["is_archived", "handled_by", "updated_at"])
    return billing