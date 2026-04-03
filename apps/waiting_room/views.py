from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.models import Role, User
from apps.notifications.services import notify_waiting_room_overload
from apps.patients.models import TriageRecord
from .forms import WaitingRoomEntryForm
from .models import WaitingRoomEntry
from .services import (
    get_active_waiting_entries,
    get_queue_position,
    waiting_room_is_overloaded,
)


@login_required
def waiting_room_list(request):
    entries = list(get_active_waiting_entries())

    entry_rows = []
    for entry in entries:
        entry_rows.append({
            "entry": entry,
            "position": get_queue_position(entry, entries),
        })

    if waiting_room_is_overloaded():
        alert_users = User.objects.filter(
            role__in=[Role.NURSE, Role.DOCTOR],
            is_active=True,
            is_verified_staff=True,
        )
        notify_waiting_room_overload(alert_users, len(entries))

    return render(
        request,
        "waiting_room/waiting_room_list.html",
        {
            "entry_rows": entry_rows,
            "is_overloaded": waiting_room_is_overloaded(),
        },
    )


@login_required
def waiting_room_add(request):
    patient_id = request.GET.get("patient")

    if request.method == "POST":
        form = WaitingRoomEntryForm(request.POST, patient_id=request.POST.get("patient"))
        if form.is_valid():
            entry = form.save(commit=False)
            entry.added_by = request.user
            try:
                entry.save()

                TriageRecord.objects.create(
                    patient=entry.patient,
                    waiting_room_entry=entry,
                    blood_pressure=form.cleaned_data.get("blood_pressure", ""),
                    pulse=form.cleaned_data.get("pulse"),
                    weight=form.cleaned_data.get("weight"),
                    body_temperature=form.cleaned_data.get("body_temperature"),
                    notes=form.cleaned_data.get("triage_notes", ""),
                    created_by=request.user,
                )

                messages.success(request, "Patient added to waiting room with vital signs.")
                return redirect("waiting_room_list")
            except ValidationError as exc:
                error_message = " ".join(exc.messages)
                form.add_error(None, error_message)
                messages.error(request, error_message)
    else:
        form = WaitingRoomEntryForm(patient_id=patient_id)

    return render(
        request,
        "waiting_room/waiting_room_form.html",
        {
            "form": form,
            "title": "Add Patient to Waiting Room",
        },
    )


@login_required
def waiting_room_remove(request, pk):
    entry = get_object_or_404(WaitingRoomEntry, pk=pk, is_active=True)
    entry.is_active = False
    entry.status = WaitingRoomEntry.Status.COMPLETED
    entry.save(update_fields=["is_active", "status"])
    messages.success(request, "Patient removed from waiting room.")
    return redirect("waiting_room_list")