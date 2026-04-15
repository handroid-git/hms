from django.urls import path

from .views import (
    notification_clear_read,
    notification_list,
    notification_mark_all_read,
    notification_mark_read,
    notification_settings,
    notification_unread_count,
)

urlpatterns = [
    path("", notification_list, name="notification_list"),
    path("settings/", notification_settings, name="notification_settings"),
    path("unread-count/", notification_unread_count, name="notification_unread_count"),
    path("<uuid:pk>/read/", notification_mark_read, name="notification_mark_read"),
    path("mark-all-read/", notification_mark_all_read, name="notification_mark_all_read"),
    path("clear-read/", notification_clear_read, name="notification_clear_read"),
]