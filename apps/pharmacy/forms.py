from django import forms
from .models import Drug, DrugIssue, PrescriptionItem


class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = [
            "name",
            "description",
            "price",
            "stock_quantity",
            "low_stock_threshold",
            "expiration_date",
            "is_available",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "description": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "expiration_date": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
        }


class PrescriptionSelectionForm(forms.Form):
    drugs = forms.ModelMultipleChoiceField(
        queryset=Drug.objects.filter(is_available=True).order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class PrescriptionItemUpdateForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ["quantity", "instructions", "status", "unavailable_note"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "instructions": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "unavailable_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = [
            (PrescriptionItem.Status.AWAITING_PAYMENT, "Awaiting Payment"),
            (PrescriptionItem.Status.READY_TO_ISSUE, "Ready To Issue"),
            (PrescriptionItem.Status.UNAVAILABLE, "Unavailable"),
        ]


class DrugIssueForm(forms.ModelForm):
    class Meta:
        model = DrugIssue
        fields = ["received_by_name", "received_by_phone", "notes"]
        widgets = {
            "received_by_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "received_by_phone": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }