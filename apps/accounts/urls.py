from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import UserLoginView, dashboard_redirect, profile_view

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard-redirect/", dashboard_redirect, name="dashboard_redirect"),
    path("profile/", profile_view, name="profile"),
]