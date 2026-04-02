from django import forms
from apps.accounts.models import Role, User
from apps.patients.models import Patient
from .models import WaitingRoomEntry


class WaitingRoomEntryForm(forms.ModelForm):
    assigned_doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role=Role.DOCTOR, is_active=True).order_by("first_name", "last_name", "username"),
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    patient = forms.ModelChoiceField(
        queryset=Patient.objects.filter(is_deceased=False).order_by("first_name", "last_name"),
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
            "priority": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        patient_id = kwargs.pop("patient_id", None)
        super().__init__(*args, **kwargs)

        if patient_id:
            try:
                self.fields["patient"].initial = self.fields["patient"].queryset.get(pk=patient_id)
            except Patient.DoesNotExist:
                pass