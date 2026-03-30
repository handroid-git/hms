from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from apps.patients.models import Patient
from apps.waiting_room.models import WaitingRoomEntry
from apps.waiting_room.services import waiting_room_is_overloaded


@login_required
def nurse_dashboard(request):
    patients_created_count = Patient.objects.filter(created_by=request.user).count()
    active_waiting_count = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).count()

    recent_patients = Patient.objects.order_by("-created_at")[:5]
    recent_waiting_entries = WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).select_related("patient").order_by("priority", "created_at")[:5]

    context = {
        "patients_created_count": patients_created_count,
        "active_waiting_count": active_waiting_count,
        "recent_patients": recent_patients,
        "recent_waiting_entries": recent_waiting_entries,
        "is_overloaded": waiting_room_is_overloaded(),
    }
    return render(request, "dashboards/nurse_dashboard.html", context)