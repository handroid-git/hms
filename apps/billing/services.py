from decimal import Decimal
from django.db import transaction
from .models import Billing, PaymentTransaction


@transaction.atomic
def update_billing_adjustments(billing, handled_by, other_charges, discount):
    billing.other_charges = other_charges
    billing.discount = discount
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