from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _


class ExtractFilterForm(forms.Form):
    q = forms.CharField(
        label=_("Pessoa ou cobrança"),
        required=False,
        max_length=120,
        widget=forms.SearchInput(
            attrs={
                "autocomplete": "off",
                "placeholder": _("Buscar pessoa ou cobrança"),
                "class": (
                    "min-h-11 w-full rounded-xl border border-pixu-border "
                    "bg-pixu-canvas px-3 py-2 text-sm text-pixu-ink "
                    "focus:border-pixu-action focus:outline-none "
                    "focus:ring-2 focus:ring-pixu-action/20"
                ),
            },
        ),
    )
    date_from = forms.DateField(
        label=_("De"),
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "min-h-11 w-full rounded-xl border border-pixu-border "
                    "bg-pixu-canvas px-3 py-2 text-sm text-pixu-ink "
                    "focus:border-pixu-action focus:outline-none "
                    "focus:ring-2 focus:ring-pixu-action/20"
                ),
            },
        ),
    )
    date_to = forms.DateField(
        label=_("Até"),
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "min-h-11 w-full rounded-xl border border-pixu-border "
                    "bg-pixu-canvas px-3 py-2 text-sm text-pixu-ink "
                    "focus:border-pixu-action focus:outline-none "
                    "focus:ring-2 focus:ring-pixu-action/20"
                ),
            },
        ),
    )

    def __init__(self, *args, include_dates: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        if not include_dates:
            self.fields.pop("date_from")
            self.fields.pop("date_to")

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error(
                "date_to",
                _("A data final deve ser igual ou posterior à inicial."),
            )
        return cleaned_data

    def mark_invalid_fields_for_accessibility(self) -> None:
        for name in self.errors:
            field = self.fields.get(name)
            if field:
                field.widget.attrs.update(
                    {
                        "aria-invalid": "true",
                        "aria-describedby": f"id_{name}_errors",
                    },
                )
