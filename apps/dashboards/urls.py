from django.urls import path

from .views import (
    accountant_dashboard,
    admin_dashboard,
    doctor_dashboard,
    doctor_dashboard_live,
    lab_dashboard,
    lab_dashboard_live,
    nurse_dashboard,
    nurse_dashboard_live,
    pharmacy_dashboard,
    pharmacy_dashboard_live,
)

urlpatterns = [
    path("nurse/", nurse_dashboard, name="nurse_dashboard"),
    path("nurse/live/", nurse_dashboard_live, name="nurse_dashboard_live"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("doctor/live/", doctor_dashboard_live, name="doctor_dashboard_live"),
    path("accountant/", accountant_dashboard, name="accountant_dashboard"),
    path("lab/", lab_dashboard, name="lab_dashboard"),
    path("lab/live/", lab_dashboard_live, name="lab_dashboard_live"),
    path("pharmacy/", pharmacy_dashboard, name="pharmacy_dashboard"),
    path("pharmacy/live/", pharmacy_dashboard_live, name="pharmacy_dashboard_live"),
    path("admin/", admin_dashboard, name="admin_dashboard"),
]