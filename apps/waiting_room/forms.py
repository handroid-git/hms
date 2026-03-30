from django import forms
from .models import WaitingRoomEntry


class WaitingRoomEntryForm(forms.ModelForm):
    class Meta:
        model = WaitingRoomEntry
        fields = ["patient", "priority"]
        widgets = {
            "patient": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "priority": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }