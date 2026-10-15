from __future__ import annotations

from decimal import Decimal

from django import forms


def format_brl_cents(value: int) -> str:
    """Format an integer amount of cents using the pt-BR convention."""
    amount = Decimal(value) / Decimal("100")
    formatted = f"{amount:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


class BrazilianDecimalField(forms.DecimalField):
    """Accept pt-BR decimals and the dotted form used by integrations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.update(
            {
                "inputmode": "numeric",
                "data-money-input": "true",
                "data-money-max-digits": str(self.max_digits or 12),
            },
        )
        self.widget.attrs.setdefault("placeholder", "0,00")

    def prepare_value(self, value):
        if isinstance(value, (int, Decimal)) and not isinstance(value, bool):
            formatted = f"{Decimal(value):,.2f}"
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return super().prepare_value(value)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace("R$", "").strip()
            if "," in value and "." in value:
                if value.rfind(",") > value.rfind("."):
                    value = value.replace(".", "").replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "," in value:
                value = value.replace(",", ".")
        return super().to_python(value)
