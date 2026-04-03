from django import forms
from apps.accounts.models import Role, User
from apps.patients.models import Patient
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason",
            "notes",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "doctor": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "appointment_date": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
            "appointment_time": forms.TimeInput(attrs={"class": "input input-bordered w-full", "type": "time"}),
            "reason": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["patient"].queryset = Patient.objects.filter(is_deceased=False).order_by("first_name", "last_name")
        self.fields["doctor"].queryset = User.objects.filter(
            role=Role.DOCTOR,
            is_active=True,
            is_verified_staff=True,
        ).order_by("first_name", "last_name", "username")


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }