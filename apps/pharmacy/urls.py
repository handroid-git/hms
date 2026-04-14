from django.urls import path
from .views import (
    drug_create,
    drug_expiry_management,
    drug_list,
    drug_restock_create,
    drug_stock_adjustment_create,
    drug_stock_movement_list,
    drug_update,
    prescription_issue_view,
    prescription_item_detail,
)

urlpatterns = [
    path("drugs/", drug_list, name="drug_list"),
    path("drugs/create/", drug_create, name="drug_create"),
    path("drugs/<uuid:pk>/update/", drug_update, name="drug_update"),
    path("drugs/restock/", drug_restock_create, name="drug_restock_create"),
    path("drugs/adjust-stock/", drug_stock_adjustment_create, name="drug_stock_adjustment_create"),
    path("drugs/expiry-management/", drug_expiry_management, name="drug_expiry_management"),
    path("stock-movements/", drug_stock_movement_list, name="drug_stock_movement_list"),
    path("prescriptions/<uuid:pk>/", prescription_item_detail, name="prescription_item_detail"),
    path("prescriptions/<uuid:pk>/issue/", prescription_issue_view, name="prescription_issue"),
]