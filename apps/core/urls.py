from django.urls import path

from .views import home, hospital_settings_view

urlpatterns = [
    path("", home, name="home"),
    path("hospital-settings/", hospital_settings_view, name="hospital_settings"),
]