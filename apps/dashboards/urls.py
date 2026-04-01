from django.urls import path
from .views import doctor_dashboard, nurse_dashboard

urlpatterns = [
    path("nurse/", nurse_dashboard, name="nurse_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
]