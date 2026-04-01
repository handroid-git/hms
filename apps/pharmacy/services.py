from decimal import Decimal
from django.db import transaction
from apps.billing.models import Billing
from .models import PrescriptionItem


@transaction.atomic
def sync_prescriptions_for_consultation(consultation, selected_drugs, prescribed_by):
    existing_items = {
        item.drug_id: item
        for item in consultation.prescription_items.select_related("drug").all()
    }
    selected_drug_ids = set(drug.pk for drug in selected_drugs)

    for drug in selected_drugs:
        if drug.pk not in existing_items:
            item = PrescriptionItem.objects.create(
                consultation=consultation,
                patient=consultation.patient,
                drug=drug,
                quantity=1,
                unit_price=drug.price,
                prescribed_by=prescribed_by,
                status=PrescriptionItem.Status.AWAITING_PAYMENT,
            )
            item.recalculate_total()
            item.save(update_fields=["total_price"])

    for drug_id, item in existing_items.items():
        if drug_id not in selected_drug_ids and item.status != PrescriptionItem.Status.ISSUED:
            item.delete()

    update_consultation_prescription_summary(consultation)
    update_billing_prescription_total(consultation)


def update_consultation_prescription_summary(consultation):
    names = [
        item.drug.name
        for item in consultation.prescription_items.exclude(status=PrescriptionItem.Status.UNAVAILABLE).select_related("drug")
    ]
    consultation.prescriptions = ", ".join(names)
    consultation.save(update_fields=["prescriptions"])


def update_billing_prescription_total(consultation):
    billing = consultation.billing
    total = sum(
        (
            item.total_price
            for item in consultation.prescription_items.exclude(status=PrescriptionItem.Status.UNAVAILABLE)
        ),
        Decimal("0.00"),
    )
    billing.prescription_total = total
    billing.recalculate_total()
    billing.save()


def prescription_is_paid(item):
    billing = item.consultation.billing
    return billing.payment_status in [
        Billing.PaymentStatus.PAID_FULL,
        Billing.PaymentStatus.PART_PAYMENT,
        Billing.PaymentStatus.DEPOSIT,
    ] and billing.amount_paid > Decimal("0.00")


@transaction.atomic
def issue_drug(item, pharmacist, received_by_name="", received_by_phone="", notes=""):
    if item.drug.stock_quantity < item.quantity:
        raise ValueError("Not enough stock to issue this drug.")

    item.drug.stock_quantity -= item.quantity
    item.drug.save(update_fields=["stock_quantity", "updated_at"])

    item.status = PrescriptionItem.Status.ISSUED
    item.save(update_fields=["status", "updated_at"])

    issue_record = item.issue_record if hasattr(item, "issue_record") else None
    if issue_record:
        issue_record.received_by_name = received_by_name
        issue_record.received_by_phone = received_by_phone
        issue_record.notes = notes
        issue_record.issued_by = pharmacist
        issue_record.save()
    else:
        from .models import DrugIssue
        DrugIssue.objects.create(
            prescription_item=item,
            issued_by=pharmacist,
            received_by_name=received_by_name,
            received_by_phone=received_by_phone,
            notes=notes,
        )

    return item