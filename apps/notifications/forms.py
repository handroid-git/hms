from django import forms
from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ["include_chat_in_general_notifications"]
        widgets = {
            "include_chat_in_general_notifications": forms.CheckboxInput(
                attrs={"class": "toggle toggle-primary"}
            ),
        }