from django import template

from pixu.contrib.currency import format_brl_cents

register = template.Library()


@register.filter
def brl_from_cents(value: int) -> str:
    return format_brl_cents(value)
