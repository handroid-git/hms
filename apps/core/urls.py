from django.urls import path

from .views import backup_center_view, home, hospital_settings_view, retention_center_view

urlpatterns = [
    path("", home, name="home"),
    path("hospital-settings/", hospital_settings_view, name="hospital_settings"),
    path("backup-center/", backup_center_view, name="backup_center"),
    path("retention-center/", retention_center_view, name="retention_center"),
]