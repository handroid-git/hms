from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import Role
from apps.dashboards.services import pharmacy_dashboard_data, pharmacy_dashboard_workflow_context

from .forms import (
    DrugForm,
    DrugInventoryFilterForm,
    DrugIssueForm,
    DrugRestockForm,
    DrugStockAdjustmentForm,
    PrescriptionItemUpdateForm,
)
from .models import Drug, DrugStockMovement, PrescriptionItem
from .services import adjust_drug_stock, issue_drug, prescription_is_paid, restock_drug


@login_required
def pharmacy_dashboard(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    context = {
        "data": pharmacy_dashboard_data(request.user),
        **pharmacy_dashboard_workflow_context(request.user),
    }
    return render(request, "dashboards/pharmacy_dashboard.html", context)


@login_required
def drug_list(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    form = DrugInventoryFilterForm(request.GET or None)
    drugs = Drug.objects.order_by("name")

    if form.is_valid():
        q = form.cleaned_data.get("q")
        stock_status = form.cleaned_data.get("stock_status")
        availability = form.cleaned_data.get("availability")

        if q:
            drugs = drugs.filter(Q(name__icontains=q) | Q(description__icontains=q))

        if availability == "available":
            drugs = drugs.filter(is_available=True)
        elif availability == "unavailable":
            drugs = drugs.filter(is_available=False)

        if stock_status == "out_of_stock":
            drugs = drugs.filter(stock_quantity=0)
        elif stock_status == "low_stock":
            drugs = [drug for drug in drugs if drug.is_low_stock and drug.stock_quantity > 0 and not drug.is_expired]
        elif stock_status == "expired":
            drugs = [drug for drug in drugs if drug.is_expired]
        elif stock_status == "near_expiry":
            drugs = [drug for drug in drugs if drug.is_near_expiry]
        elif stock_status == "in_stock":
            drugs = [drug for drug in drugs if drug.stock_quantity > 0 and not drug.is_low_stock and not drug.is_expired]

    return render(
        request,
        "pharmacy/drug_list.html",
        {
            "drugs": drugs,
            "filter_form": form,
        },
    )


@login_required
def drug_create(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = DrugForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Drug created successfully.")
            return redirect("drug_list")
    else:
        form = DrugForm()

    return render(request, "pharmacy/drug_form.html", {"form": form, "title": "Create Drug"})


@login_required
def drug_update(request, pk):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    drug = get_object_or_404(Drug, pk=pk)

    if request.method == "POST":
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            form.save()
            messages.success(request, "Drug updated successfully.")
            return redirect("drug_list")
    else:
        form = DrugForm(instance=drug)

    return render(request, "pharmacy/drug_form.html", {"form": form, "title": "Update Drug"})


@login_required
def prescription_item_detail(request, pk):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    item = get_object_or_404(
        PrescriptionItem.objects.select_related(
            "patient",
            "drug",
            "consultation",
            "consultation__billing",
        ),
        pk=pk,
    )

    paid = prescription_is_paid(item)

    if request.method == "POST":
        form = PrescriptionItemUpdateForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            if item.status == PrescriptionItem.Status.READY_TO_ISSUE and not paid:
                messages.error(request, "This prescription cannot be marked ready to issue until payment exists.")
            else:
                item.save()
                messages.success(request, "Prescription item updated successfully.")
                return redirect("prescription_item_detail", pk=item.pk)
    else:
        form = PrescriptionItemUpdateForm(instance=item)

    issue_form = DrugIssueForm()

    return render(
        request,
        "pharmacy/prescription_item_detail.html",
        {
            "item": item,
            "form": form,
            "issue_form": issue_form,
            "paid": paid,
        },
    )


@login_required
def prescription_issue_view(request, pk):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    item = get_object_or_404(
        PrescriptionItem.objects.select_related(
            "drug",
            "consultation",
            "consultation__billing",
        ),
        pk=pk,
    )

    if not prescription_is_paid(item):
        messages.error(request, "Payment has not been made for this prescription.")
        return redirect("prescription_item_detail", pk=item.pk)

    if request.method == "POST":
        form = DrugIssueForm(request.POST)
        if form.is_valid():
            try:
                issue_drug(
                    item=item,
                    pharmacist=request.user,
                    received_by_name=form.cleaned_data["received_by_name"],
                    received_by_phone=form.cleaned_data["received_by_phone"],
                    notes=form.cleaned_data["notes"],
                )
                messages.success(request, "Drug issued successfully.")
            except ValueError as exc:
                messages.error(request, str(exc))
            return redirect("prescription_item_detail", pk=item.pk)

    return redirect("prescription_item_detail", pk=item.pk)


@login_required
def drug_restock_create(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = DrugRestockForm(request.POST)
        if form.is_valid():
            try:
                restock_drug(
                    drug=form.cleaned_data["drug"],
                    quantity_added=form.cleaned_data["quantity_added"],
                    pharmacist=request.user,
                    unit_cost=form.cleaned_data.get("unit_cost") or Decimal("0.00"),
                    supplier_name=form.cleaned_data.get("supplier_name", ""),
                    batch_number=form.cleaned_data.get("batch_number", ""),
                    expiration_date=form.cleaned_data.get("expiration_date"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Drug restocked successfully.")
                return redirect("drug_stock_movement_list")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = DrugRestockForm()

    return render(
        request,
        "pharmacy/drug_restock_form.html",
        {
            "form": form,
            "title": "Restock Drug",
        },
    )


@login_required
def drug_stock_adjustment_create(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = DrugStockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                adjust_drug_stock(
                    drug=form.cleaned_data["drug"],
                    quantity_change=form.cleaned_data["quantity_change"],
                    pharmacist=request.user,
                    reason=form.cleaned_data["reason"],
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Drug stock adjusted successfully.")
                return redirect("drug_stock_movement_list")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = DrugStockAdjustmentForm()

    return render(
        request,
        "pharmacy/drug_stock_adjustment_form.html",
        {
            "form": form,
            "title": "Adjust Drug Stock",
        },
    )


@login_required
def drug_stock_movement_list(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    movements = DrugStockMovement.objects.select_related(
        "drug",
        "performed_by",
        "prescription_item",
        "restock_record",
    )
    return render(
        request,
        "pharmacy/drug_stock_movement_list.html",
        {
            "movements": movements,
        },
    )


@login_required
def drug_expiry_management(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    today = timezone.localdate()
    drugs = Drug.objects.order_by("expiration_date", "name")
    expired_drugs = [drug for drug in drugs if drug.is_expired]
    near_expiry_drugs = [drug for drug in drugs if drug.is_near_expiry]
    no_expiry_drugs = [drug for drug in drugs if not drug.expiration_date]

    return render(
        request,
        "pharmacy/drug_expiry_management.html",
        {
            "today": today,
            "expired_drugs": expired_drugs,
            "near_expiry_drugs": near_expiry_drugs,
            "no_expiry_drugs": no_expiry_drugs,
        },
    )