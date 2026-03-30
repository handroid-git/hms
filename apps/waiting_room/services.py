from .models import WaitingRoomEntry


WAITING_ROOM_ALERT_THRESHOLD = 10


def get_active_waiting_entries():
    return WaitingRoomEntry.objects.filter(
        is_active=True,
        status=WaitingRoomEntry.Status.WAITING
    ).select_related("patient", "added_by").order_by("priority", "created_at")


def get_waiting_room_count():
    return get_active_waiting_entries().count()


def waiting_room_is_overloaded():
    return get_waiting_room_count() > WAITING_ROOM_ALERT_THRESHOLD


def remove_entry_from_waiting_room(entry):
    entry.is_active = False
    entry.status = WaitingRoomEntry.Status.COMPLETED
    entry.save(update_fields=["is_active", "status"])


def get_queue_position(entry, queryset=None):
    if queryset is None:
        queryset = list(get_active_waiting_entries())
    else:
        queryset = list(queryset)

    for index, item in enumerate(queryset, start=1):
        if item.pk == entry.pk:
            return index
    return None