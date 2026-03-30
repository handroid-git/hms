from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from .forms import LoginForm, ProfileUpdateForm
from .models import Role


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = False


@login_required
def dashboard_redirect(request):
    role = request.user.role

    if role == Role.NURSE:
        return redirect("nurse_dashboard")
    elif role == Role.DOCTOR:
        return redirect("admin:index")
    elif role == Role.ACCOUNTANT:
        return redirect("admin:index")
    elif role == Role.LAB_TECHNICIAN:
        return redirect("admin:index")
    elif role == Role.PHARMACIST:
        return redirect("admin:index")
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