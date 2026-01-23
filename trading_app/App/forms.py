# -------------------------------------------------------------------------------
#                                 forms.py                                       
# -------------------------------------------------------------------------------

from django import forms
from .models import Stock, Trade


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = "__all__"
        widgets = {
            "symbol": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_symbol",
                "placeholder": "add stock symbol",
                "autocomplete": "off"
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_name",
                "placeholder": "add stock name",
                "autocomplete": "off"
            }),
            "current_price": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_current_price",
                "step": "0.01",
                "readonly": True,
            }),
            "high": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_high",
                "step": "0.01"
            }),
            "low": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_low",
                "step": "0.01"
            }),
            "rsi": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_rsi",
                "step": "0.01"
            }),
            "tp1": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_tp1",
                "step": "0.01"
            }),
            "tp2": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_tp2",
                "step": "0.01"
            }),
            "tp3": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_tp3",
                "step": "0.01"
            }),
            "sl1": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_sl1",
                "step": "0.01"
            }),
            "sl2": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_sl2",
                "step": "0.01"
            }),
            "sl3": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "id_sl3",
                "step": "0.01"
            }),
        }


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            "stock",
            "quantity",
            "buying_price",
            "buy_date",
            "mtp",
            "msl",
            "comments",
        ]
        widgets = {
            "stock": forms.Select(attrs={
                "class": "form-select",
                "id": "id_stock"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1"
            }),
            "buying_price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "buy_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "mtp": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "msl": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "comments": forms.Textarea(attrs={
                "class": "form-control",
                "rows": "3",
                "placeholder": "Trade reasoning, strategy or notes..."
            }),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None or quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean_buying_price(self):
        buying_price = self.cleaned_data.get("buying_price")
        if buying_price is not None and buying_price < 0:
            raise forms.ValidationError("Buying price cannot be negative.")
        return buying_price

    def clean_mtp(self):
        mtp = self.cleaned_data.get("mtp")
        if mtp is not None and mtp < 0:
            raise forms.ValidationError("Target price cannot be negative.")
        return mtp

    def clean_msl(self):
        msl = self.cleaned_data.get("msl")
        if msl is not None and msl < 0:
            raise forms.ValidationError("Stop loss cannot be negative.")
        return msl
