from django.urls import path
from .views import (
    drug_create,
    drug_list,
    drug_update,
    prescription_issue_view,
    prescription_item_detail,
)

urlpatterns = [
    path("drugs/", drug_list, name="drug_list"),
    path("drugs/create/", drug_create, name="drug_create"),
    path("drugs/<uuid:pk>/update/", drug_update, name="drug_update"),
    path("prescriptions/<uuid:pk>/", prescription_item_detail, name="prescription_item_detail"),
    path("prescriptions/<uuid:pk>/issue/", prescription_issue_view, name="prescription_issue"),
]