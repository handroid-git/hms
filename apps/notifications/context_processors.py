from .services import get_general_unread_notifications_count


def notification_counts(request):
    if request.user.is_authenticated:
        unread_notifications_count = get_general_unread_notifications_count(request.user)
        return {
            "unread_notifications_count": unread_notifications_count,
        }

    return {
        "unread_notifications_count": 0,
    }