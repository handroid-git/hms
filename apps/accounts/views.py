from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.notifications.forms import NotificationPreferenceForm
from apps.notifications.services import get_or_create_notification_preference

from .forms import LoginForm, ProfileUpdateForm, StaffSignupForm
from .models import Role


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session["dashboard_welcome_until"] = (
            timezone.now() + timedelta(minutes=5)
        ).isoformat()
        return response


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = StaffSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your staff account request was submitted successfully. Please wait for administrator verification.",
            )
            return redirect("login")
    else:
        form = StaffSignupForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard_redirect(request):
    role = request.user.role

    if role == Role.NURSE:
        return redirect("nurse_dashboard")
    elif role == Role.DOCTOR:
        return redirect("doctor_dashboard")
    elif role == Role.ACCOUNTANT:
        return redirect("accountant_dashboard")
    elif role == Role.LAB_TECHNICIAN:
        return redirect("lab_dashboard")
    elif role == Role.PHARMACIST:
        return redirect("pharmacy_dashboard")
    elif role == Role.ADMIN:
        return redirect("admin:index")

    return redirect("login")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
def app_settings_view(request):
    preference = get_or_create_notification_preference(request.user)

    if request.method == "POST":
        notification_form = NotificationPreferenceForm(request.POST, instance=preference)
        if notification_form.is_valid():
            notification_form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect("app_settings")
    else:
        notification_form = NotificationPreferenceForm(instance=preference)

    return render(
        request,
        "accounts/settings.html",
        {
            "notification_form": notification_form,
        },
    )