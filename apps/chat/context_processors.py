from .models import Message


def chat_counts(request):
    if not request.user.is_authenticated:
        return {
            "unread_chat_count": 0,
        }

    unread_chat_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()

    return {
        "unread_chat_count": unread_chat_count,
    }