from django.urls import path
from .views import nurse_dashboard

urlpatterns = [
    path("nurse/", nurse_dashboard, name="nurse_dashboard"),
]