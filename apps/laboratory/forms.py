from django import forms

from .models import LabRequestItem, LabTest, LabTestRestock


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        if data:
            return [single_file_clean(data, initial)]
        return []


class LabResultUpdateForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={"class": "file-input file-input-bordered w-full", "multiple": True}),
    )

    class Meta:
        model = LabRequestItem
        fields = ["result_text", "status", "unavailable_note"]
        widgets = {
            "result_text": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "unavailable_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = [
            (LabRequestItem.Status.IN_PROGRESS, "In Progress"),
            (LabRequestItem.Status.READY, "Ready for Doctor Review"),
            (LabRequestItem.Status.UNAVAILABLE, "Not Available"),
        ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        result_text = cleaned_data.get("result_text")
        attachments = cleaned_data.get("attachments", [])
        unavailable_note = cleaned_data.get("unavailable_note")

        if status == LabRequestItem.Status.READY and not result_text and not attachments:
            self.add_error("result_text", "Provide result text or upload at least one file before marking ready.")

        if status == LabRequestItem.Status.UNAVAILABLE and not unavailable_note:
            self.add_error("unavailable_note", "Please explain why this test is not available.")

        return cleaned_data


class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = [
            "name",
            "description",
            "price",
            "is_available",
            "stock_quantity",
            "low_stock_threshold",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "description": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
        }


class LabTestRestockForm(forms.ModelForm):
    class Meta:
        model = LabTestRestock
        fields = [
            "lab_test",
            "quantity_added",
            "supplier_name",
            "batch_number",
            "notes",
        ]
        widgets = {
            "lab_test": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "quantity_added": forms.NumberInput(attrs={"class": "input input-bordered w-full", "min": "1"}),
            "supplier_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "batch_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def clean_quantity_added(self):
        quantity = self.cleaned_data["quantity_added"]
        if quantity <= 0:
            raise forms.ValidationError("Quantity added must be greater than zero.")
        return quantity


class LabStockAdjustmentForm(forms.Form):
    lab_test = forms.ModelChoiceField(
        queryset=LabTest.objects.order_by("name"),
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    quantity_change = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
        help_text="Use positive numbers to increase stock and negative numbers to reduce stock.",
    )
    reason = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        initial="Manual stock adjustment",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
    )

    def clean_quantity_change(self):
        quantity_change = self.cleaned_data["quantity_change"]
        if quantity_change == 0:
            raise forms.ValidationError("Quantity change cannot be zero.")
        return quantity_change


class LabInventoryFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "Search by lab test name"}),
    )
    stock_status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All stock statuses"),
            ("in_stock", "In Stock"),
            ("low_stock", "Low Stock"),
            ("out_of_stock", "Out of Stock"),
        ],
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    availability = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All availability"),
            ("available", "Available"),
            ("unavailable", "Unavailable"),
        ],
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )