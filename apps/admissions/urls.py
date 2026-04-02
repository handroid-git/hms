from django.urls import path
from .views import (
    admission_create_from_consultation_view,
    admission_detail,
    admission_list,
    discharge_admission_view,
    inpatient_note_create_view,
    medication_administration_create_view,
)

urlpatterns = [
    path("", admission_list, name="admission_list"),
    path("<uuid:pk>/", admission_detail, name="admission_detail"),
    path("consultation/<uuid:consultation_pk>/create/", admission_create_from_consultation_view, name="admission_create_from_consultation"),
    path("<uuid:admission_pk>/notes/<str:note_type>/create/", inpatient_note_create_view, name="inpatient_note_create"),
    path("<uuid:admission_pk>/medications/create/", medication_administration_create_view, name="medication_administration_create"),
    path("<uuid:admission_pk>/discharge/", discharge_admission_view, name="discharge_admission"),
]