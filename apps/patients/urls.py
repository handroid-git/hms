from django.urls import path
from .views import (
    patient_create,
    patient_detail,
    patient_list,
    patient_record_create,
    patient_update,
)

urlpatterns = [
    path("", patient_list, name="patient_list"),
    path("create/", patient_create, name="patient_create"),
    path("<uuid:pk>/", patient_detail, name="patient_detail"),
    path("<uuid:pk>/update/", patient_update, name="patient_update"),
    path("<uuid:patient_pk>/records/create/", patient_record_create, name="patient_record_create"),
]