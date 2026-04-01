from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from .forms import LoginForm, ProfileUpdateForm, StaffSignupForm
from .models import Role


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = False


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = StaffSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your staff account request has been submitted and is awaiting administrator verification."
            )
            return redirect("pending_verification")
    else:
        form = StaffSignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def pending_verification_view(request):
    return render(request, "accounts/pending_verification.html")


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

    messages.warning(request, "Your account role is not configured correctly.")
    return redirect("profile")


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