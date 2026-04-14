from decimal import Decimal

from django import forms

from .models import Drug, DrugRestock, PrescriptionItem


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


class PrescriptionItemUpdateForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ["status", "unavailable_note", "instructions", "quantity"]
        widgets = {
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "unavailable_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "instructions": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
            "quantity": forms.NumberInput(attrs={"class": "input input-bordered w-full", "min": "1"}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity


class DrugIssueForm(forms.Form):
    received_by_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"}),
    )
    received_by_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
    )


class DrugRestockForm(forms.ModelForm):
    class Meta:
        model = DrugRestock
        fields = [
            "drug",
            "quantity_added",
            "unit_cost",
            "supplier_name",
            "batch_number",
            "expiration_date",
            "notes",
        ]
        widgets = {
            "drug": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "quantity_added": forms.NumberInput(attrs={"class": "input input-bordered w-full", "min": "1"}),
            "unit_cost": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "0.01"}),
            "supplier_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "batch_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "expiration_date": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def clean_quantity_added(self):
        quantity = self.cleaned_data["quantity_added"]
        if quantity <= 0:
            raise forms.ValidationError("Quantity added must be greater than zero.")
        return quantity

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get("unit_cost") or Decimal("0.00")
        if unit_cost < Decimal("0.00"):
            raise forms.ValidationError("Unit cost cannot be negative.")
        return unit_cost


class DrugStockAdjustmentForm(forms.Form):
    drug = forms.ModelChoiceField(
        queryset=Drug.objects.order_by("name"),
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


class DrugInventoryFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "Search by drug name"}),
    )
    stock_status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All stock statuses"),
            ("in_stock", "In Stock"),
            ("low_stock", "Low Stock"),
            ("out_of_stock", "Out of Stock"),
            ("expired", "Expired"),
            ("near_expiry", "Near Expiry"),
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