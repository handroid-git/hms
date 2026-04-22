from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from apps.notifications.forms import NotificationPreferenceForm
from apps.notifications.services import get_or_create_notification_preference

from .forms import (
    DoctorConsultationFeeFilterForm,
    DoctorConsultationFeeForm,
    LoginForm,
    ProfileUpdateForm,
    StaffSignupForm,
    StyledPasswordChangeForm,
)
from .models import Role, User, VerificationStatus


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


class UserPasswordChangeView(PasswordChangeView):
    template_name = "accounts/change_password.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("change_password")

    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        return super().form_valid(form)


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
        return redirect("admin_dashboard")

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

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "can_manage_doctor_fees": request.user.role in [Role.ACCOUNTANT, Role.ADMIN] or request.user.is_superuser,
        },
    )


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
            "can_manage_doctor_fees": request.user.role in [Role.ACCOUNTANT, Role.ADMIN] or request.user.is_superuser,
        },
    )


@login_required
def doctor_fee_list_view(request):
    if request.user.role not in [Role.ACCOUNTANT, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    filter_form = DoctorConsultationFeeFilterForm(request.GET or None)
    doctors = User.objects.filter(role=Role.DOCTOR).order_by("first_name", "last_name", "username")

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            doctors = doctors.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(username__icontains=q)
                | Q(employee_id__icontains=q)
            )

    return render(
        request,
        "accounts/doctor_fee_list.html",
        {
            "doctors": doctors,
            "filter_form": filter_form,
        },
    )


@login_required
def doctor_fee_update_view(request, pk):
    if request.user.role not in [Role.ACCOUNTANT, Role.ADMIN] and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    doctor = get_object_or_404(User, pk=pk, role=Role.DOCTOR)

    if request.method == "POST":
        form = DoctorConsultationFeeForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor consultation fee updated successfully.")
            return redirect("doctor_fee_list")
    else:
        form = DoctorConsultationFeeForm(instance=doctor)

    return render(
        request,
        "accounts/doctor_fee_form.html",
        {
            "doctor": doctor,
            "form": form,
        },
    )


# =========================
# STAFF ADMIN (STEP 9)
# =========================

@login_required
def staff_list_view(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    q = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")

    users = User.objects.all().order_by("-date_joined")

    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(employee_id__icontains=q)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        users = users.filter(verification_status=status_filter)

    return render(
        request,
        "accounts/staff_list.html",
        {
            "users": users,
            "roles": Role.choices,
            "statuses": VerificationStatus.choices,
        },
    )


@login_required
def staff_approve_view(request, pk):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    user = get_object_or_404(User, pk=pk)
    user.approve(request.user)

    messages.success(request, f"{user.username} approved successfully.")
    return redirect("staff_list")


@login_required
def staff_reject_view(request, pk):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    user = get_object_or_404(User, pk=pk)
    user.reject(request.user)

    messages.success(request, f"{user.username} rejected.")
    return redirect("staff_list")


@login_required
def staff_toggle_active_view(request, pk):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    messages.success(
        request,
        f"{user.username} {'activated' if user.is_active else 'deactivated'}.",
    )
    return redirect("staff_list")