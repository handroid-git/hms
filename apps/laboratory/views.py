from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import Role
from .forms import LabResultUpdateForm, LabTestForm
from .models import LabRequest, LabRequestItem, LabTest
from .services import (
    doctor_accept_result,
    doctor_reject_result,
    technician_update_result_item,
)


@login_required
def lab_dashboard(request):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    active_requests = LabRequest.objects.filter(
        status__in=[
            LabRequest.Status.PENDING,
            LabRequest.Status.IN_PROGRESS,
            LabRequest.Status.REJECTED,
        ]
    ).select_related("patient", "consultation").order_by("-updated_at")

    available_tests = LabTest.objects.order_by("name")
    low_stock_tests = [test for test in available_tests if test.is_low_stock]

    today = timezone.localdate()
    completed_today = LabRequestItem.objects.filter(
        uploaded_by=request.user,
        status=LabRequestItem.Status.ACCEPTED,
        doctor_reviewed_at__date=today,
    ).count()

    completed_all_time = LabRequestItem.objects.filter(
        uploaded_by=request.user,
        status=LabRequestItem.Status.ACCEPTED,
    ).count()

    context = {
        "active_requests": active_requests,
        "available_tests": available_tests[:10],
        "low_stock_tests": low_stock_tests,
        "completed_today": completed_today,
        "completed_all_time": completed_all_time,
    }
    return render(request, "laboratory/lab_dashboard.html", context)


@login_required
def lab_request_detail(request, pk):
    if request.user.role != Role.LAB_TECHNICIAN:
        return render(request, "dashboards/access_denied.html", status=403)

    lab_request = get_object_or_404(
        LabRequest.objects.select_related("patient", "consultation", "requested_by"),
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
        LabRequestItem.objects.select_related("lab_request", "lab_test").prefetch_related("attachments"),
        pk=item_pk,
    )

    if request.method == "POST":
        form = LabResultUpdateForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            technician_update_result_item(item, form, request.FILES, request.user)
            messages.success(request, "Lab result updated successfully.")
            return redirect("lab_request_detail", pk=item.lab_request.pk)
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

    tests = LabTest.objects.order_by("name")
    return render(request, "laboratory/lab_test_list.html", {"tests": tests})


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