from django import forms

from .models import BackupOperationLog, HospitalSetting


class HospitalSettingForm(forms.ModelForm):
    class Meta:
        model = HospitalSetting
        fields = [
            "hospital_name",
            "short_name",
            "hospital_address",
            "hospital_phone",
            "hospital_email",
            "hospital_website",
            "hospital_motto",
            "hospital_logo",
            "currency_symbol",
            "timezone_label",
            "default_e_card_fee",
            "record_retention_days",
            "backup_instructions",
        ]
        widgets = {
            "hospital_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "short_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "hospital_address": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "hospital_phone": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "hospital_email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "hospital_website": forms.URLInput(attrs={"class": "input input-bordered w-full"}),
            "hospital_motto": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "hospital_logo": forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
            "currency_symbol": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "timezone_label": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "default_e_card_fee": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "step": "0.01", "min": "0"}
            ),
            "record_retention_days": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": "1"}
            ),
            "backup_instructions": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 5}),
        }

    def clean_default_e_card_fee(self):
        value = self.cleaned_data["default_e_card_fee"]
        if value < 0:
            raise forms.ValidationError("Default E-card fee cannot be negative.")
        return value

    def clean_record_retention_days(self):
        value = self.cleaned_data["record_retention_days"]
        if value <= 0:
            raise forms.ValidationError("Record retention days must be greater than zero.")
        return value


class BackupOperationLogForm(forms.ModelForm):
    class Meta:
        model = BackupOperationLog
        fields = [
            "operation_type",
            "file_type",
            "title",
            "file_path",
            "status",
            "notes",
        ]
        widgets = {
            "operation_type": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "file_type": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "file_path": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": r"Example: C:\Backups\hms_backup_2026_04_18.sqlite3",
                }
            ),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title is required.")
        return title