from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from pixu.contrib.currency import BrazilianDecimalField
from pixu.contrib.currency import format_brl_cents

from .models import PAYMENT_REFERENCE_MAX_LENGTH
from .services import CompensationOption
from .services import payment_balance
from .validators import validate_receipt

RECEIPT_INPUT_ATTRS = {
    "accept": ".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png",
    "class": "peer sr-only",
    "data-file-input": "true",
}


class PaymentForm(forms.Form):
    amount = BrazilianDecimalField(
        label=_("Valor enviado em reais"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        localize=True,
        widget=forms.TextInput(
            attrs={"inputmode": "decimal", "autocomplete": "off"},
        ),
    )
    reference = forms.CharField(
        label=_("Referência (opcional)"),
        max_length=PAYMENT_REFERENCE_MAX_LENGTH,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    receipt = forms.FileField(
        label=_("Comprovante (opcional)"),
        required=False,
        help_text=_("PDF, JPEG ou PNG dentro do limite configurado."),
        widget=forms.FileInput(attrs=RECEIPT_INPUT_ATTRS),
    )

    def __init__(self, debt, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debt = debt
        self.balance = payment_balance(debt)
        self.fields["amount"].help_text = _(
            "Disponível para registrar: %(amount)s.",
        ) % {"amount": f"R$ {format_brl_cents(self.balance.available_cents)}"}

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data["amount"]
        cents = amount * 100
        if cents != cents.to_integral_value():
            raise ValidationError(_("Use no máximo duas casas decimais."))
        if int(cents) > self.balance.available_cents:
            raise ValidationError(_("O valor excede o disponível para esta dívida."))
        return amount

    def clean_reference(self) -> str:
        return self.cleaned_data["reference"].strip()

    def clean_receipt(self):
        receipt = self.cleaned_data.get("receipt")
        if receipt:
            validate_receipt(receipt)
        return receipt

    @property
    def amount_cents(self) -> int:
        return int(self.cleaned_data["amount"] * 100)


class ReceiptForm(forms.Form):
    receipt = forms.FileField(
        label=_("Novo comprovante"),
        help_text=_("PDF, JPEG ou PNG dentro do limite configurado."),
        widget=forms.FileInput(attrs=RECEIPT_INPUT_ATTRS),
    )

    def clean_receipt(self):
        receipt = self.cleaned_data["receipt"]
        validate_receipt(receipt)
        return receipt


class CompensationForm(forms.Form):
    reciprocal_debt_id = forms.IntegerField(widget=forms.HiddenInput)
    request_id = forms.UUIDField(widget=forms.HiddenInput)
    amount = BrazilianDecimalField(
        label=_("Valor a compensar em reais"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        localize=True,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}),
    )

    def __init__(self, option: CompensationOption, *args, **kwargs):
        initial = {
            "reciprocal_debt_id": option.reciprocal_debt.pk,
            "request_id": uuid4(),
            "amount": Decimal(option.max_amount_cents) / Decimal("100"),
            **kwargs.pop("initial", {}),
        }
        super().__init__(*args, initial=initial, **kwargs)
        self.option = option
        self.fields["amount"].help_text = _(
            "Máximo disponível nas duas dívidas: %(amount)s.",
        ) % {"amount": f"R$ {format_brl_cents(option.max_amount_cents)}"}

    def clean_reciprocal_debt_id(self) -> int:
        reciprocal_debt_id = self.cleaned_data["reciprocal_debt_id"]
        if reciprocal_debt_id != self.option.reciprocal_debt.pk:
            raise ValidationError(_("Atualize a dívida inversa antes de continuar."))
        return reciprocal_debt_id

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data["amount"]
        cents = amount * 100
        if cents != cents.to_integral_value():
            raise ValidationError(_("Use no máximo duas casas decimais."))
        if int(cents) > self.option.max_amount_cents:
            raise ValidationError(_("O valor excede o disponível nas duas dívidas."))
        return amount

    @property
    def amount_cents(self) -> int:
        return int(self.cleaned_data["amount"] * 100)
