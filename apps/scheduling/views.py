from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import Role
from .forms import AppointmentForm, AppointmentStatusForm
from .models import Appointment
from .services import (
    cancel_appointment,
    check_in_appointment,
    complete_appointment,
    reassign_appointment_if_needed,
)


@login_required
def appointment_list(request):
    today = timezone.localdate()

    if request.user.role == Role.DOCTOR:
        appointments = Appointment.objects.filter(
            doctor=request.user,
        ).select_related("patient", "doctor", "reassigned_to").order_by("appointment_date", "appointment_time")
    else:
        appointments = Appointment.objects.select_related(
            "patient", "doctor", "reassigned_to"
        ).order_by("appointment_date", "appointment_time")

    today_appointments = appointments.filter(appointment_date=today)
    upcoming_appointments = appointments.filter(appointment_date__gt=today, status__in=[
        Appointment.Status.SCHEDULED,
        Appointment.Status.REASSIGNED,
    ])[:20]

    return render(
        request,
        "scheduling/appointment_list.html",
        {
            "today_appointments": today_appointments,
            "upcoming_appointments": upcoming_appointments,
        },
    )


@login_required
def appointment_create(request):
    if request.user.role not in [Role.DOCTOR, Role.NURSE, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.save()
            reassign_appointment_if_needed(appointment)
            messages.success(request, "Appointment scheduled successfully.")
            return redirect("appointment_list")
    else:
        form = AppointmentForm()

    return render(
        request,
        "scheduling/appointment_form.html",
        {
            "form": form,
            "title": "Schedule Appointment",
        },
    )


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor", "created_by", "reassigned_to"),
        pk=pk,
    )

    if request.user.role == Role.DOCTOR and appointment.doctor != request.user and appointment.reassigned_to != request.user:
        return render(request, "dashboards/access_denied.html", status=403)

    form = AppointmentStatusForm(instance=appointment)

    return render(
        request,
        "scheduling/appointment_detail.html",
        {
            "appointment": appointment,
            "form": form,
        },
    )


@login_required
def appointment_check_in(request, pk):
    if request.user.role not in [Role.NURSE, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    appointment = get_object_or_404(Appointment, pk=pk)
    check_in_appointment(appointment, request.user)
    messages.success(request, "Patient checked in and added to the waiting room.")
    return redirect("appointment_detail", pk=appointment.pk)


@login_required
def appointment_complete_view(request, pk):
    if request.user.role not in [Role.DOCTOR, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    appointment = get_object_or_404(Appointment, pk=pk)
    complete_appointment(appointment)
    messages.success(request, "Appointment marked as completed.")
    return redirect("appointment_detail", pk=appointment.pk)


@login_required
def appointment_cancel_view(request, pk):
    if request.user.role not in [Role.DOCTOR, Role.NURSE, Role.ADMIN]:
        return render(request, "dashboards/access_denied.html", status=403)

    appointment = get_object_or_404(Appointment, pk=pk)
    cancel_appointment(appointment)
    messages.success(request, "Appointment cancelled.")
    return redirect("appointment_detail", pk=appointment.pk)