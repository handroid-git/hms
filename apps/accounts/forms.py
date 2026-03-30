from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input input-bordered w-full",
        "placeholder": "Username"
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "input input-bordered w-full",
        "placeholder": "Password"
    }))


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "profile_picture",
            "shift_start",
            "shift_end",
            "shift_days",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "phone_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "shift_start": forms.TimeInput(attrs={"class": "input input-bordered w-full", "type": "time"}),
            "shift_end": forms.TimeInput(attrs={"class": "input input-bordered w-full", "type": "time"}),
            "shift_days": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": 'Example: ["Monday", "Tuesday"]'
            }),
        }