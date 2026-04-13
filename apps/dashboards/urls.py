from django.urls import path

from .views import (
    accountant_dashboard,
    admin_dashboard,
    doctor_dashboard,
    lab_dashboard,
    nurse_dashboard,
    pharmacy_dashboard,
)

urlpatterns = [
    path("nurse/", nurse_dashboard, name="nurse_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("accountant/", accountant_dashboard, name="accountant_dashboard"),
    path("lab/", lab_dashboard, name="lab_dashboard"),
    path("pharmacy/", pharmacy_dashboard, name="pharmacy_dashboard"),
    path("admin/", admin_dashboard, name="admin_dashboard"),
]