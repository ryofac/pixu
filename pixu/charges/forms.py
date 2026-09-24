from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from pixu.accounts.models import User

from .models import Charge
from .models import Participation


class ChargeCreateForm(forms.Form):
    title = forms.CharField(label=_("Título"), max_length=120)
    description = forms.CharField(
        label=_("Descrição"),
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    total = forms.DecimalField(
        label=_("Valor total em reais"),
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        localize=True,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}),
    )
    invitees = forms.ModelMultipleChoiceField(
        label=_("Convidar pessoas cadastradas"),
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, actor: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields["invitees"].queryset = (
            User.objects.filter(is_active=True)
            .exclude(pk=actor.pk)
            .order_by("username")
        )

    def clean_total(self) -> Decimal:
        total = self.cleaned_data["total"]
        cents = total * 100
        if cents != cents.to_integral_value():
            raise ValidationError(_("Use no máximo duas casas decimais."))
        return total

    @property
    def total_cents(self) -> int:
        return int(self.cleaned_data["total"] * 100)

    @property
    def invitee_ids(self) -> list[int]:
        return [user.pk for user in self.cleaned_data["invitees"]]


class ChargeSharesForm(forms.Form):
    """Dynamic form for the creator's and pending participants' quotas."""

    def __init__(self, charge: Charge, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.charge = charge
        self.participations = list(
            charge.participations.exclude(state=Participation.State.DECLINED)
            .select_related("user")
            .order_by("pk"),
        )
        for participation in self.participations:
            self.fields[self.field_name(participation.pk)] = forms.DecimalField(
                label=participation.user.name or participation.user.username,
                max_digits=12,
                decimal_places=2,
                min_value=Decimal("0.00"),
                localize=True,
                initial=Decimal(participation.share_cents) / 100,
                disabled=(
                    participation.user_id != charge.creator_id
                    and participation.state == Participation.State.ACCEPTED
                ),
            )

    @staticmethod
    def field_name(participation_id: int) -> str:
        return f"share_{participation_id}"

    def clean(self):
        cleaned_data = super().clean()
        shares = self.shares_by_participation
        if len(shares) == len(self.participations) and sum(shares.values()) != self.charge.total_cents:
            raise ValidationError(_("A soma das cotas deve ser igual ao total da cobrança."))
        return cleaned_data

    @property
    def shares_by_participation(self) -> dict[int, int]:
        shares = {}
        for participation in self.participations:
            amount = self.cleaned_data.get(self.field_name(participation.pk))
            if amount is not None:
                shares[participation.pk] = int(amount * 100)
        return shares


class ReplaceParticipantForm(forms.Form):
    replacement = forms.ModelChoiceField(
        label=_("Convidar outra pessoa"),
        queryset=User.objects.none(),
    )

    def __init__(self, charge: Charge, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        current_user_ids = charge.participations.values_list("user_id", flat=True)
        self.fields["replacement"].queryset = (
            User.objects.filter(is_active=True)
            .exclude(pk=charge.creator_id)
            .exclude(pk__in=current_user_ids)
            .order_by("username")
        )
