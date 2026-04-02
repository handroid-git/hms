from django import forms
from .models import Admission, InpatientNote, MedicationAdministration


class AdmissionCreateForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ["reason_for_admission", "ward", "bed_number"]
        widgets = {
            "reason_for_admission": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
            "ward": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "bed_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        }


class AdmissionDischargeForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ["discharge_summary"]
        widgets = {
            "discharge_summary": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }


class InpatientNoteForm(forms.ModelForm):
    class Meta:
        model = InpatientNote
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }


class MedicationAdministrationForm(forms.ModelForm):
    class Meta:
        model = MedicationAdministration
        fields = [
            "medication_name",
            "dosage",
            "frequency",
            "route",
            "administration_notes",
        ]
        widgets = {
            "medication_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "dosage": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "frequency": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "route": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "administration_notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }