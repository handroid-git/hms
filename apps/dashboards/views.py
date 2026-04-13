from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import Role
from .services import (
    accountant_dashboard_data,
    admin_dashboard_data,
    doctor_dashboard_data,
    lab_dashboard_data,
    lab_dashboard_workflow_context,
    nurse_dashboard_data,
    pharmacy_dashboard_data,
    pharmacy_dashboard_workflow_context,
)


@login_required
def access_denied(request):
    return render(request, "dashboards/access_denied.html", status=403)


@login_required
def nurse_dashboard(request):
    if request.user.role not in [Role.NURSE, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    return render(
        request,
        "dashboards/nurse_dashboard.html",
        {"data": nurse_dashboard_data(request.user)},
    )


@login_required
def doctor_dashboard(request):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    return render(
        request,
        "dashboards/doctor_dashboard.html",
        {"data": doctor_dashboard_data(request.user)},
    )


@login_required
def accountant_dashboard(request):
    if request.user.role not in [Role.ACCOUNTANT, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    return render(
        request,
        "dashboards/accountant_dashboard.html",
        {"data": accountant_dashboard_data(request.user)},
    )


@login_required
def lab_dashboard(request):
    if request.user.role not in [Role.LAB_TECHNICIAN, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    context = {
        "data": lab_dashboard_data(request.user),
        **lab_dashboard_workflow_context(request.user),
    }
    return render(request, "dashboards/lab_dashboard.html", context)


@login_required
def pharmacy_dashboard(request):
    if request.user.role not in [Role.PHARMACIST, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    context = {
        "data": pharmacy_dashboard_data(request.user),
        **pharmacy_dashboard_workflow_context(request.user),
    }
    return render(request, "dashboards/pharmacy_dashboard.html", context)


@login_required
def admin_dashboard(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    return render(
        request,
        "dashboards/admin_dashboard.html",
        {"data": admin_dashboard_data(request.user)},
    )