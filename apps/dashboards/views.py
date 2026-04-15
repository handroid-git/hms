from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from apps.accounts.models import Role
from apps.consultations.models import Consultation

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
def nurse_dashboard_live(request):
    if request.user.role not in [Role.NURSE, Role.ADMIN] and not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)

    data = nurse_dashboard_data(request.user)
    return JsonResponse(
        {
            "total_patients_created": data["total_patients_created"],
            "patients_created_today": data["patients_created_today"],
            "patients_created_month": data["patients_created_month"],
            "total_triaged": data["total_triaged"],
            "triaged_today": data["triaged_today"],
            "active_waiting_room_count": data["active_waiting_room_count"],
            "my_active_waiting_room_count": data["my_active_waiting_room_count"],
            "discharge_pending_count": data["discharge_pending_count"],
            "outstanding_patient_balances": str(data["outstanding_patient_balances"]),
        }
    )


@login_required
def doctor_dashboard(request):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    ongoing_consultations = Consultation.objects.select_related(
        "patient",
        "waiting_room_entry",
    ).filter(
        doctor=request.user,
        status=Consultation.Status.IN_PROGRESS,
        complete=False,
    ).order_by("-updated_at")

    return render(
        request,
        "dashboards/doctor_dashboard.html",
        {
            "data": doctor_dashboard_data(request.user),
            "ongoing_consultations": ongoing_consultations[:5],
            "ongoing_consultations_count": ongoing_consultations.count(),
        },
    )


@login_required
def doctor_dashboard_live(request):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN] and not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)

    data = doctor_dashboard_data(request.user)
    ongoing_consultations = Consultation.objects.select_related(
        "patient",
        "waiting_room_entry",
    ).filter(
        doctor=request.user,
        status=Consultation.Status.IN_PROGRESS,
        complete=False,
    ).order_by("-updated_at")

    ongoing_html = render_to_string(
        "dashboards/partials/doctor_ongoing_consultations_table.html",
        {
            "ongoing_consultations": ongoing_consultations[:5],
        },
        request=request,
    )

    return JsonResponse(
        {
            "total_consulted": data["total_consulted"],
            "consultations_today": data["consultations_today"],
            "consultations_month": data["consultations_month"],
            "avg_per_day": data["avg_per_day"],
            "total_bills": str(data["total_bills"]),
            "admissions_count": data["admissions_count"],
            "pending_lab_reviews": data["pending_lab_reviews"],
            "active_waiting_room_count": data["active_waiting_room_count"],
            "ongoing_consultations_count": ongoing_consultations.count(),
            "ongoing_html": ongoing_html,
        }
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
def lab_dashboard_live(request):
    if request.user.role not in [Role.LAB_TECHNICIAN, Role.ADMIN] and not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)

    data = lab_dashboard_data(request.user)
    workflow = lab_dashboard_workflow_context(request.user)

    active_requests_html = render_to_string(
        "dashboards/partials/lab_active_requests_table.html",
        {
            "active_requests": workflow["active_requests"],
        },
        request=request,
    )

    pending_items_html = render_to_string(
        "dashboards/partials/lab_pending_items_table.html",
        {
            "pending_items": workflow["pending_items"],
        },
        request=request,
    )

    return JsonResponse(
        {
            "completed_today": workflow["completed_today"],
            "completed_all_time": workflow["completed_all_time"],
            "available_tests": data["available_tests"],
            "tests_today": data["tests_today"],
            "tests_month": data["tests_month"],
            "tests_total": data["tests_total"],
            "pending_tests": data["pending_tests"],
            "rejected_tests": data["rejected_tests"],
            "unavailable_tests": data["unavailable_tests"],
            "low_stock_tests_count": data["low_stock_tests_count"],
            "out_of_stock_tests_count": data["out_of_stock_tests_count"],
            "recent_restock_count": data["recent_restock_count"],
            "show_low_stock_alert": bool(workflow["low_stock_tests"]),
            "active_requests_html": active_requests_html,
            "pending_items_html": pending_items_html,
        }
    )


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
def pharmacy_dashboard_live(request):
    if request.user.role not in [Role.PHARMACIST, Role.ADMIN] and not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)

    data = pharmacy_dashboard_data(request.user)
    workflow = pharmacy_dashboard_workflow_context(request.user)

    pending_items_html = render_to_string(
        "dashboards/partials/pharmacy_pending_items_table.html",
        {
            "pending_items": workflow["pending_items"],
        },
        request=request,
    )

    return JsonResponse(
        {
            "issued_today": workflow["issued_today"],
            "issued_all_time": workflow["issued_all_time"],
            "total_drugs": data["total_drugs"],
            "available_drugs": data["available_drugs"],
            "low_stock": data["low_stock"],
            "out_of_stock": data["out_of_stock"],
            "near_expiry_count": data["near_expiry_count"],
            "expired_count": data["expired_count"],
            "recent_restock_count": data["recent_restock_count"],
            "show_low_stock_alert": bool(workflow["low_stock_drugs"]),
            "show_expired_alert": bool(workflow["expired_drugs"]),
            "show_near_expiry_alert": bool(workflow["near_expiry_drugs"]),
            "pending_items_html": pending_items_html,
        }
    )


@login_required
def admin_dashboard(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    return render(
        request,
        "dashboards/admin_dashboard.html",
        {"data": admin_dashboard_data(request.user)},
    )