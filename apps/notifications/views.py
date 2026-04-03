from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])

    if notification.link:
        return redirect(notification.link)
    return redirect("notification_list")


@login_required
def notification_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notification_list")


@login_required
def notification_clear_read(request):
    if request.method == "POST":
        request.user.notifications.filter(is_read=True).delete()
    return redirect("notification_list")


@login_required
def notification_unread_count(request):
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"unread_count": unread_count})