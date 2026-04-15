from decimal import Decimal

from django.db import transaction

from apps.billing.models import Billing
from .models import DrugIssue, DrugRestock, DrugStockMovement, PrescriptionItem


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
        else:
            existing_item = existing_items[drug.pk]
            if existing_item.unit_price != drug.price:
                existing_item.unit_price = drug.price
                existing_item.recalculate_total()
                existing_item.save(update_fields=["unit_price", "total_price", "updated_at"])

    for drug_id, item in existing_items.items():
        if drug_id not in selected_drug_ids and item.status != PrescriptionItem.Status.ISSUED:
            item.delete()

    update_consultation_prescription_summary(consultation)
    update_billing_prescription_total(consultation)


@transaction.atomic
def update_prescription_details_from_post(consultation, post_data):
    items = consultation.prescription_items.select_related("drug").all()

    for item in items:
        drug_key = str(item.drug_id)

        dosage = (post_data.get(f"prescription_dosage_{drug_key}") or "").strip()
        frequency = (post_data.get(f"prescription_frequency_{drug_key}") or "").strip()
        route = (post_data.get(f"prescription_route_{drug_key}") or "").strip()
        instructions = (post_data.get(f"prescription_instructions_{drug_key}") or "").strip()
        quantity_raw = (post_data.get(f"prescription_quantity_{drug_key}") or "1").strip()
        duration_raw = (post_data.get(f"prescription_duration_days_{drug_key}") or "").strip()

        if not dosage:
            raise ValueError(f"Please enter dosage for {item.drug.name}.")
        if not frequency:
            raise ValueError(f"Please enter frequency for {item.drug.name}.")

        try:
            quantity = int(quantity_raw)
        except ValueError as exc:
            raise ValueError(f"Quantity for {item.drug.name} must be a whole number.") from exc

        if quantity <= 0:
            raise ValueError(f"Quantity for {item.drug.name} must be greater than zero.")

        duration_days = None
        if duration_raw:
            try:
                duration_days = int(duration_raw)
            except ValueError as exc:
                raise ValueError(f"Duration for {item.drug.name} must be a whole number.") from exc
            if duration_days <= 0:
                raise ValueError(f"Duration for {item.drug.name} must be greater than zero.")

        item.dosage = dosage
        item.frequency = frequency
        item.route = route
        item.instructions = instructions
        item.quantity = quantity
        item.duration_days = duration_days
        item.unit_price = item.drug.price
        item.recalculate_total()
        item.save(
            update_fields=[
                "dosage",
                "frequency",
                "route",
                "instructions",
                "quantity",
                "duration_days",
                "unit_price",
                "total_price",
                "updated_at",
            ]
        )

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
def create_drug_stock_movement(
    *,
    drug,
    movement_type,
    quantity,
    previous_stock,
    new_stock,
    performed_by=None,
    reason="",
    notes="",
    prescription_item=None,
    restock_record=None,
):
    return DrugStockMovement.objects.create(
        drug=drug,
        movement_type=movement_type,
        quantity=quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        performed_by=performed_by,
        reason=reason,
        notes=notes,
        prescription_item=prescription_item,
        restock_record=restock_record,
    )


@transaction.atomic
def restock_drug(
    *,
    drug,
    quantity_added,
    pharmacist=None,
    unit_cost=Decimal("0.00"),
    supplier_name="",
    batch_number="",
    expiration_date=None,
    notes="",
):
    if quantity_added <= 0:
        raise ValueError("Restock quantity must be greater than zero.")

    previous_stock = drug.stock_quantity
    drug.stock_quantity += quantity_added

    if expiration_date:
        drug.expiration_date = expiration_date

    drug.is_available = drug.stock_quantity > 0 and not drug.is_expired
    drug.save(update_fields=["stock_quantity", "expiration_date", "is_available", "updated_at"])

    restock_record = DrugRestock.objects.create(
        drug=drug,
        quantity_added=quantity_added,
        unit_cost=unit_cost,
        supplier_name=supplier_name,
        batch_number=batch_number,
        expiration_date=expiration_date,
        notes=notes,
        restocked_by=pharmacist,
    )

    create_drug_stock_movement(
        drug=drug,
        movement_type=DrugStockMovement.MovementType.RESTOCK,
        quantity=quantity_added,
        previous_stock=previous_stock,
        new_stock=drug.stock_quantity,
        performed_by=pharmacist,
        reason="Drug restock",
        notes=notes,
        restock_record=restock_record,
    )

    return restock_record


@transaction.atomic
def adjust_drug_stock(
    *,
    drug,
    quantity_change,
    pharmacist=None,
    reason="Manual stock adjustment",
    notes="",
):
    previous_stock = drug.stock_quantity
    new_stock = previous_stock + quantity_change

    if new_stock < 0:
        raise ValueError("Stock adjustment would make stock negative.")

    drug.stock_quantity = new_stock
    drug.is_available = drug.stock_quantity > 0 and not drug.is_expired
    drug.save(update_fields=["stock_quantity", "is_available", "updated_at"])

    create_drug_stock_movement(
        drug=drug,
        movement_type=DrugStockMovement.MovementType.ADJUSTMENT,
        quantity=quantity_change,
        previous_stock=previous_stock,
        new_stock=new_stock,
        performed_by=pharmacist,
        reason=reason,
        notes=notes,
    )

    return drug


@transaction.atomic
def issue_drug(item, pharmacist, received_by_name="", received_by_phone="", notes=""):
    if item.drug.is_expired:
        raise ValueError("This drug is expired and cannot be issued.")

    if item.drug.stock_quantity < item.quantity:
        raise ValueError("Not enough stock to issue this drug.")

    previous_stock = item.drug.stock_quantity
    item.drug.stock_quantity -= item.quantity
    item.drug.is_available = item.drug.stock_quantity > 0 and not item.drug.is_expired
    item.drug.save(update_fields=["stock_quantity", "is_available", "updated_at"])

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
        issue_record = DrugIssue.objects.create(
            prescription_item=item,
            issued_by=pharmacist,
            received_by_name=received_by_name,
            received_by_phone=received_by_phone,
            notes=notes,
        )

    create_drug_stock_movement(
        drug=item.drug,
        movement_type=DrugStockMovement.MovementType.ISSUE,
        quantity=-int(item.quantity),
        previous_stock=previous_stock,
        new_stock=item.drug.stock_quantity,
        performed_by=pharmacist,
        reason="Drug issued to patient",
        notes=notes,
        prescription_item=item,
    )

    return item