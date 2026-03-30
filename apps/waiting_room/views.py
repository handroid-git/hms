from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
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
    if request.method == "POST":
        form = WaitingRoomEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.added_by = request.user
            entry.save()
            messages.success(request, "Patient added to waiting room.")
            return redirect("waiting_room_list")
    else:
        form = WaitingRoomEntryForm()

    return render(
        request,
        "patients/patient_form.html",
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