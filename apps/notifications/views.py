from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NotificationPreferenceForm
from .models import Notification
from .services import get_general_unread_notifications_count, get_or_create_notification_preference


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    unread_count = request.user.notifications.filter(is_read=False).count()

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
    unread_count = get_general_unread_notifications_count(request.user)
    return JsonResponse(
        {
            "unread_count": unread_count,
        }
    )


@login_required
def notification_settings(request):
    preference = get_or_create_notification_preference(request.user)

    if request.method == "POST":
        form = NotificationPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification settings updated successfully.")
            return redirect("notification_settings")
    else:
        form = NotificationPreferenceForm(instance=preference)

    return render(
        request,
        "notifications/notification_settings.html",
        {
            "form": form,
        },
    )