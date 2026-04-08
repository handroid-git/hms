from django import forms
from apps.accounts.models import User
from .models import Message


class StartConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, is_verified_staff=True).order_by("first_name", "last_name", "username"),
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full",
                    "rows": 4,
                    "placeholder": "Type your message...",
                }
            ),
        }