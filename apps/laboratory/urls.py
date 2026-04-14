from django.urls import path
from .views import (
    doctor_accept_lab_result,
    doctor_reject_lab_result,
    lab_request_detail,
    lab_result_update,
    lab_stock_movement_list,
    lab_test_create,
    lab_test_list,
    lab_test_restock_create,
    lab_test_stock_adjustment_create,
    lab_test_update,
)

urlpatterns = [
    path("requests/<uuid:pk>/", lab_request_detail, name="lab_request_detail"),
    path("results/<uuid:item_pk>/update/", lab_result_update, name="lab_result_update"),
    path("results/<uuid:item_pk>/accept/", doctor_accept_lab_result, name="doctor_accept_lab_result"),
    path("results/<uuid:item_pk>/reject/", doctor_reject_lab_result, name="doctor_reject_lab_result"),
    path("tests/", lab_test_list, name="lab_test_list"),
    path("tests/create/", lab_test_create, name="lab_test_create"),
    path("tests/<uuid:pk>/update/", lab_test_update, name="lab_test_update"),
    path("tests/restock/", lab_test_restock_create, name="lab_test_restock_create"),
    path("tests/adjust-stock/", lab_test_stock_adjustment_create, name="lab_test_stock_adjustment_create"),
    path("stock-movements/", lab_stock_movement_list, name="lab_stock_movement_list"),
]