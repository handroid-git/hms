from django import forms
from apps.accounts.models import User
from .models import PayrollRecord, StaffSalaryStructure


class StaffSalaryStructureForm(forms.ModelForm):
    class Meta:
        model = StaffSalaryStructure
        fields = ["staff", "base_salary", "is_active", "effective_from", "notes"]
        widgets = {
            "staff": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "base_salary": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "effective_from": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["staff"].queryset = User.objects.filter(
            is_active=True,
            is_verified_staff=True,
        ).order_by("first_name", "last_name", "username")


class PayrollGenerateForm(forms.Form):
    year = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"})
    )
    month = forms.IntegerField(
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"})
    )


class PayrollUpdateForm(forms.ModelForm):
    class Meta:
        model = PayrollRecord
        fields = ["bonus", "deduction", "accountant_note"]
        widgets = {
            "bonus": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "deduction": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "accountant_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }