from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Role
from apps.dashboards.services import lab_dashboard_data, lab_dashboard_workflow_context

from .forms import (
    LabInventoryFilterForm,
    LabResultUpdateForm,
    LabStockAdjustmentForm,
    LabTestForm,
    LabTestRestockForm,
)
from .models import LabRequest, LabRequestItem, LabStockMovement, LabTest
from .services import (
    adjust_lab_test_stock,
    doctor_accept_result,
    doctor_reject_result,
    restock_lab_test,
    technician_update_result_item,
)


@login_required
def lab_dashboard(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    context = {
        "data": lab_dashboard_data(request.user),
        **lab_dashboard_workflow_context(request.user),
    }
    return render(request, "dashboards/lab_dashboard.html", context)


@login_required
def lab_request_detail(request, pk):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    lab_request = get_object_or_404(
        LabRequest.objects.select_related(
            "patient",
            "consultation",
            "requested_by",
            "consultation__billing",
        ),
        pk=pk,
    )
    items = lab_request.items.select_related("lab_test").prefetch_related("attachments").all()

    return render(
        request,
        "laboratory/lab_request_detail.html",
        {
            "lab_request": lab_request,
            "items": items,
        },
    )


@login_required
def lab_result_update(request, item_pk):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    item = get_object_or_404(
        LabRequestItem.objects.select_related(
            "lab_request",
            "lab_test",
            "lab_request__consultation",
            "lab_request__consultation__billing",
        ).prefetch_related("attachments"),
        pk=item_pk,
    )

    if request.method == "POST":
        form = LabResultUpdateForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            try:
                technician_update_result_item(item, form, request.FILES, request.user)
                messages.success(request, "Lab result updated successfully.")
                return redirect("lab_request_detail", pk=item.lab_request.pk)
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = LabResultUpdateForm(instance=item)

    return render(
        request,
        "laboratory/lab_result_form.html",
        {
            "form": form,
            "item": item,
        },
    )


@login_required
def lab_test_list(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    form = LabInventoryFilterForm(request.GET or None)
    tests = LabTest.objects.order_by("name")

    if form.is_valid():
        q = form.cleaned_data.get("q")
        stock_status = form.cleaned_data.get("stock_status")
        availability = form.cleaned_data.get("availability")

        if q:
            tests = tests.filter(Q(name__icontains=q) | Q(description__icontains=q))

        if availability == "available":
            tests = tests.filter(is_available=True)
        elif availability == "unavailable":
            tests = tests.filter(is_available=False)

        if stock_status == "out_of_stock":
            tests = tests.filter(stock_quantity=0)
        elif stock_status == "low_stock":
            tests = [test for test in tests if test.is_low_stock and test.stock_quantity > 0]
        elif stock_status == "in_stock":
            tests = [test for test in tests if test.stock_quantity > 0 and not test.is_low_stock]

    return render(
        request,
        "laboratory/lab_test_list.html",
        {
            "tests": tests,
            "filter_form": form,
        },
    )


@login_required
def lab_test_create(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = LabTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lab test created successfully.")
            return redirect("lab_test_list")
    else:
        form = LabTestForm()

    return render(
        request,
        "laboratory/lab_test_form.html",
        {"form": form, "title": "Create Lab Test"},
    )


@login_required
def lab_test_update(request, pk):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    test = get_object_or_404(LabTest, pk=pk)

    if request.method == "POST":
        form = LabTestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, "Lab test updated successfully.")
            return redirect("lab_test_list")
    else:
        form = LabTestForm(instance=test)

    return render(
        request,
        "laboratory/lab_test_form.html",
        {"form": form, "title": "Update Lab Test"},
    )


@login_required
def doctor_accept_lab_result(request, item_pk):
    if request.user.role != Role.DOCTOR:
        return render(request, "dashboards/access_denied.html", status=403)

    item = get_object_or_404(
        LabRequestItem.objects.select_related("lab_request", "lab_request__consultation"),
        pk=item_pk,
    )

    doctor_accept_result(item, request.user)
    messages.success(request, "Lab result accepted.")
    return redirect("consultation_detail", pk=item.lab_request.consultation.pk)


@login_required
def doctor_reject_lab_result(request, item_pk):
    if request.user.role != Role.DOCTOR:
        return render(request, "dashboards/access_denied.html", status=403)

    item = get_object_or_404(
        LabRequestItem.objects.select_related("lab_request", "lab_request__consultation"),
        pk=item_pk,
    )

    doctor_reject_result(item, request.user)
    messages.warning(request, "Lab result rejected and returned to laboratory.")
    return redirect("consultation_detail", pk=item.lab_request.consultation.pk)


@login_required
def lab_test_restock_create(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = LabTestRestockForm(request.POST)
        if form.is_valid():
            try:
                restock_lab_test(
                    lab_test=form.cleaned_data["lab_test"],
                    quantity_added=form.cleaned_data["quantity_added"],
                    lab_technician=request.user,
                    supplier_name=form.cleaned_data.get("supplier_name", ""),
                    batch_number=form.cleaned_data.get("batch_number", ""),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Lab test stock restocked successfully.")
                return redirect("lab_stock_movement_list")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = LabTestRestockForm()

    return render(
        request,
        "laboratory/lab_test_restock_form.html",
        {
            "form": form,
            "title": "Restock Lab Test",
        },
    )


@login_required
def lab_test_stock_adjustment_create(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = LabStockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                adjust_lab_test_stock(
                    lab_test=form.cleaned_data["lab_test"],
                    quantity_change=form.cleaned_data["quantity_change"],
                    lab_technician=request.user,
                    reason=form.cleaned_data["reason"],
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Lab stock adjusted successfully.")
                return redirect("lab_stock_movement_list")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = LabStockAdjustmentForm()

    return render(
        request,
        "laboratory/lab_stock_adjustment_form.html",
        {
            "form": form,
            "title": "Adjust Lab Stock",
        },
    )


@login_required
def lab_stock_movement_list(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    movements = LabStockMovement.objects.select_related(
        "lab_test",
        "performed_by",
        "lab_request_item",
        "restock_record",
    )
    return render(
        request,
        "laboratory/lab_stock_movement_list.html",
        {
            "movements": movements,
        },
    )