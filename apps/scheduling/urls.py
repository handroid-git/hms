from django.urls import path
from .views import (
    appointment_cancel_view,
    appointment_check_in,
    appointment_create,
    appointment_detail,
    appointment_list,
    appointment_complete_view,
)

urlpatterns = [
    path("", appointment_list, name="appointment_list"),
    path("create/", appointment_create, name="appointment_create"),
    path("<uuid:pk>/", appointment_detail, name="appointment_detail"),
    path("<uuid:pk>/check-in/", appointment_check_in, name="appointment_check_in"),
    path("<uuid:pk>/complete/", appointment_complete_view, name="appointment_complete"),
    path("<uuid:pk>/cancel/", appointment_cancel_view, name="appointment_cancel"),
]