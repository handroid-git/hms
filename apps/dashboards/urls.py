from django.urls import path
from .views import accountant_dashboard, doctor_dashboard, nurse_dashboard

urlpatterns = [
    path("nurse/", nurse_dashboard, name="nurse_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("accountant/", accountant_dashboard, name="accountant_dashboard"),
]