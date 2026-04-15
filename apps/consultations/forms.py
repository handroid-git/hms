from django import forms

from apps.laboratory.models import LabTest
from apps.pharmacy.models import Drug

from .models import Consultation


class ConsultationUpdateForm(forms.ModelForm):
    selected_lab_tests = forms.ModelMultipleChoiceField(
        queryset=LabTest.objects.filter(is_available=True).order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    selected_drugs = forms.ModelMultipleChoiceField(
        queryset=Drug.objects.filter(is_available=True).order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Consultation
        fields = [
            "complaint",
            "diagnosis",
            "medication",
            "notes",
            "admitted",
            "discharged",
            "died",
        ]
        widgets = {
            "complaint": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "diagnosis": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "medication": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        consultation = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        if consultation and consultation.pk:
            existing_request = consultation.lab_requests.first()
            if existing_request:
                self.fields["selected_lab_tests"].initial = [
                    item.lab_test.pk for item in existing_request.items.all()
                ]

            self.fields["selected_drugs"].initial = [
                item.drug.pk for item in consultation.prescription_items.all()
            ]

    def clean(self):
        cleaned_data = super().clean()
        admitted = cleaned_data.get("admitted")
        medication = cleaned_data.get("medication")

        if medication and not admitted:
            self.add_error("medication", "Medication can only be added after the patient is marked as admitted.")

        return cleaned_data