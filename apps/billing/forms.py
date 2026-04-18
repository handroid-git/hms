from django import forms

from .models import Billing, BillingExtraItem, PaymentTransaction


class BillingUpdateForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ["consultation_fee", "e_card_fee", "other_charges", "discount"]
        widgets = {
            "consultation_fee": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "e_card_fee": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "other_charges": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "discount": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
        }


class BillingExtraItemForm(forms.ModelForm):
    class Meta:
        model = BillingExtraItem
        fields = ["title", "price"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "price": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
        }


class BillingExtraItemUpdateForm(forms.ModelForm):
    class Meta:
        model = BillingExtraItem
        fields = ["title", "price"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "price": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
        }


class PaymentTransactionForm(forms.ModelForm):
    class Meta:
        model = PaymentTransaction
        fields = ["amount", "payment_type", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "payment_type": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount


class BillingNoteForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ["internal_note"]
        widgets = {
            "internal_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }