from django import forms
from .models import Patient, PatientRecord


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "hospital_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone_number",
            "address",
            "next_of_kin",
            "next_of_kin_phone",
            "admission_status",
            "given_birth",
            "is_deceased",
        ]
        widgets = {
            "hospital_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "date_of_birth": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
            "gender": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "phone_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "address": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "next_of_kin": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "next_of_kin_phone": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "admission_status": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }


class PatientRecordForm(forms.ModelForm):
    class Meta:
        model = PatientRecord
        fields = [
            "blood_pressure",
            "pulse",
            "weight",
            "body_temperature",
            "diagnosis",
            "medication",
            "laboratory_tests",
            "admitted",
            "discharged",
            "died",
            "given_birth",
        ]
        widgets = {
            "blood_pressure": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "pulse": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "weight": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "body_temperature": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.1"}),
            "diagnosis": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "medication": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "laboratory_tests": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }