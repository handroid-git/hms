from django.urls import path
from .views import (
    consultation_complete_view,
    consultation_detail,
    doctor_consultation_start,
)

urlpatterns = [
    path("start/", doctor_consultation_start, name="doctor_consultation_start"),
    path("<uuid:pk>/", consultation_detail, name="consultation_detail"),
    path("<uuid:pk>/complete/", consultation_complete_view, name="consultation_complete"),
]