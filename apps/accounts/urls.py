from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    UserLoginView,
    app_settings_view,
    dashboard_redirect,
    profile_view,
    signup_view,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard-redirect/", dashboard_redirect, name="dashboard_redirect"),
    path("profile/", profile_view, name="profile"),
    path("settings/", app_settings_view, name="app_settings"),
]