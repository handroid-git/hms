from django import forms
from apps.accounts.models import Role, User
from .models import WaitingRoomEntry


class WaitingRoomEntryForm(forms.ModelForm):
    assigned_doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role=Role.DOCTOR, is_active=True).order_by("first_name", "last_name", "username"),
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    blood_pressure = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"})
    )
    pulse = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"})
    )
    weight = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"})
    )
    body_temperature = forms.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=1,
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.1"})
    )
    triage_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3})
    )

    class Meta:
        model = WaitingRoomEntry
        fields = ["patient", "priority", "assigned_doctor"]
        widgets = {
            "patient": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "priority": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }