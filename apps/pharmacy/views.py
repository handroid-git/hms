from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import Role
from apps.dashboards.services import pharmacy_dashboard_data

from .forms import DrugForm, DrugIssueForm, PrescriptionItemUpdateForm
from .models import Drug, PrescriptionItem
from .services import issue_drug, prescription_is_paid


@login_required
def pharmacy_dashboard(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    pending_items = PrescriptionItem.objects.filter(
        status__in=[
            PrescriptionItem.Status.AWAITING_PAYMENT,
            PrescriptionItem.Status.READY_TO_ISSUE,
            PrescriptionItem.Status.UNAVAILABLE,
        ]
    ).select_related("patient", "drug", "consultation").order_by("-updated_at")

    available_drugs = Drug.objects.order_by("name")
    low_stock_drugs = [drug for drug in available_drugs if drug.is_low_stock]
    expired_drugs = [drug for drug in available_drugs if drug.is_expired]

    today = timezone.localdate()
    issued_today = PrescriptionItem.objects.filter(
        status=PrescriptionItem.Status.ISSUED,
        issue_record__issued_by=request.user,
        issue_record__issued_at__date=today,
    ).count()

    issued_all_time = PrescriptionItem.objects.filter(
        status=PrescriptionItem.Status.ISSUED,
        issue_record__issued_by=request.user,
    ).count()

    context = {
        "pending_items": pending_items,
        "low_stock_drugs": low_stock_drugs,
        "expired_drugs": expired_drugs,
        "issued_today": issued_today,
        "issued_all_time": issued_all_time,
        "data": pharmacy_dashboard_data(request.user),
    }
    return render(request, "pharmacy/pharmacy_dashboard.html", context)


@login_required
def drug_list(request):
    if request.user.role != Role.PHARMACIST:
        return render(request, "dashboards/access_denied.html", status=403)

    drugs = Drug.objects.order_by("name")
    return render(request, "pharmacy/drug_list.html", {"drugs": drugs})


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