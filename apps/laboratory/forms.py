from django import forms
from .models import LabRequestItem, LabTest


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []

        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            cleaned_files = [single_file_clean(file_item, initial) for file_item in data if file_item]
            return cleaned_files

        return [single_file_clean(data, initial)]


class LabResultUpdateForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "file-input file-input-bordered w-full",
                "multiple": True,
            }
        ),
    )

    class Meta:
        model = LabRequestItem
        fields = ["result_text", "status", "unavailable_note"]
        widgets = {
            "result_text": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 4}
            ),
            "status": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
            "unavailable_note": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
            ),
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
        unavailable_note = cleaned_data.get("unavailable_note")
        uploaded_files = cleaned_data.get("attachments", [])

        if status == LabRequestItem.Status.READY and not result_text and not uploaded_files and not self.instance.attachments.exists():
            self.add_error(
                "result_text",
                "Provide result text or upload at least one file before marking ready.",
            )

        if status == LabRequestItem.Status.UNAVAILABLE and not unavailable_note:
            self.add_error(
                "unavailable_note",
                "Please explain why this test is not available.",
            )

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
            "description": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 3}
            ),
            "price": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "step": "0.01"}
            ),
            "stock_quantity": forms.NumberInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "low_stock_threshold": forms.NumberInput(
                attrs={"class": "input input-bordered w-full"}
            ),
        }