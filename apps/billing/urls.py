from django.urls import path
from .views import archived_billing_list, billing_dashboard, billing_detail, billing_list

urlpatterns = [
    path("dashboard/", billing_dashboard, name="billing_dashboard"),
    path("", billing_list, name="billing_list"),
    path("archived/", archived_billing_list, name="archived_billing_list"),
    path("<uuid:pk>/", billing_detail, name="billing_detail"),
]