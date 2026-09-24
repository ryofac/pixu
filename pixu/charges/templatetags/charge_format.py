from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def brl_from_cents(value: int) -> str:
    amount = Decimal(value) / Decimal(100)
    formatted = f"{amount:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
