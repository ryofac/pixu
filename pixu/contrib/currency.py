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
