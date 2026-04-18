from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import Role

from .forms import HospitalSettingForm
from .models import HospitalSetting


def home(request):
    return render(request, "core/home.html")


@login_required
def hospital_settings_view(request):
    if request.user.role != Role.ADMIN and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    hospital_settings = HospitalSetting.get_solo()

    if request.method == "POST":
        form = HospitalSettingForm(request.POST, request.FILES, instance=hospital_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Hospital operational settings updated successfully.")
    else:
        form = HospitalSettingForm(instance=hospital_settings)

    return render(
        request,
        "core/hospital_settings.html",
        {
            "form": form,
            "hospital_settings": hospital_settings,
        },
    )