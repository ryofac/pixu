from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from pixu.accounts.models import User
from pixu.contrib.currency import BrazilianDecimalField

from .models import CHARGE_CANCELLATION_REASON_MAX_LENGTH
from .models import CHARGE_DESCRIPTION_MAX_LENGTH
from .models import CHARGE_TITLE_MAX_LENGTH
from .models import Charge
from .models import Participation
from .services import calculate_shares


class ChargeCreateForm(forms.Form):
    title = forms.CharField(label=_("Título"), max_length=CHARGE_TITLE_MAX_LENGTH)
    description = forms.CharField(
        label=_("Descrição"),
        max_length=CHARGE_DESCRIPTION_MAX_LENGTH,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    total = BrazilianDecimalField(
        label=_("Valor total em reais"),
        help_text=_("Use reais e centavos, por exemplo: 150,00."),
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
    creditor = forms.ModelChoiceField(
        label=_("Quem recebe"),
        help_text=_("Escolha quem deve receber os pagamentos desta cobrança."),
        queryset=User.objects.none(),
        empty_label=None,
    )
    include_creator = forms.BooleanField(
        label=_("Também participo do rateio"),
        help_text=_(
            "Desmarque se o total deve ser dividido somente entre os convidados.",
        ),
        initial=True,
        required=False,
    )

    def __init__(self, actor: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields["creditor"].queryset = User.objects.filter(is_active=True).order_by(
            "username",
        )
        self.fields["creditor"].label_from_instance = lambda user: (
            f"{user.name} (Você)" if user.pk == actor.pk and user.name
            else f"{user.username} (Você)" if user.pk == actor.pk
            else f"{user.name} ({user.username})" if user.name
            else user.username
        )
        self.fields["creditor"].initial = actor.pk
        self.fields["invitees"].queryset = (
            User.objects.filter(is_active=True)
            .exclude(pk=actor.pk)
            .order_by("username")
        )
        self.fields["invitees"].label_from_instance = lambda user: (
            f"{user.name} ({user.username})" if user.name else user.username
        )

    def clean_total(self) -> Decimal:
        total = self.cleaned_data["total"]
        cents = total * 100
        if cents != cents.to_integral_value():
            raise ValidationError(_("Use no máximo duas casas decimais."))
        return total

    def clean(self):
        cleaned_data = super().clean()
        if (
            "invitees" in cleaned_data
            and not cleaned_data.get("include_creator")
            and not cleaned_data["invitees"]
        ):
            self.add_error("invitees", _("Inclua ao menos uma pessoa no rateio."))
        return cleaned_data

    @property
    def participants(self):
        people = list(self.cleaned_data["invitees"])
        if self.cleaned_data.get("include_creator"):
            people.append(self.actor)
        return sorted(people, key=lambda person: person.pk)

    @property
    def total_cents(self) -> int:
        return int(self.cleaned_data["total"] * 100)

    @property
    def invitee_ids(self) -> list[int]:
        return [user.pk for user in self.cleaned_data["invitees"]]


class ChargeSharesForm(forms.Form):
    """Dynamic form for the creator's and pending participants' quotas."""

    creditor = forms.ModelChoiceField(
        label=_("Quem recebe"),
        queryset=User.objects.none(),
        empty_label=None,
    )

    def __init__(self, charge: Charge, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.charge = charge
        self.participations = list(
            charge.participations.exclude(state=Participation.State.DECLINED)
            .select_related("user")
            .order_by("pk"),
        )
        self.fields["creditor"].queryset = User.objects.filter(
            Q(is_active=True) | Q(pk=charge.creditor_id),
        ).order_by("username")
        self.fields["creditor"].initial = charge.creditor_id
        self.fields["creditor"].disabled = any(
            participation.user_id != charge.creator_id
            and participation.state == Participation.State.ACCEPTED
            for participation in self.participations
        )
        self.fields["creditor"].help_text = (
            _("O recebedor não pode mudar depois do aceite de outra pessoa.")
            if self.fields["creditor"].disabled
            else _("Pode mudar até o aceite de outra pessoa, antes de pagamentos.")
        )
        for participation in self.participations:
            self.fields[self.field_name(participation.pk)] = BrazilianDecimalField(
                label=participation.user.name or participation.user.username,
                max_digits=12,
                decimal_places=2,
                min_value=Decimal("0.00"),
                localize=True,
                initial=Decimal(participation.share_cents) / 100,
                widget=forms.TextInput(attrs={"inputmode": "decimal"}),
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
        if (
            self.fields["creditor"].disabled
            and "creditor" in self.data
            and str(self.data["creditor"]) != str(self.charge.creditor_id)
        ):
            self.add_error(
                "creditor",
                _("O recebedor não pode mudar depois do aceite de outra pessoa."),
            )
        shares = self.shares_by_participation
        if (
            len(shares) == len(self.participations)
            and sum(shares.values()) != self.charge.total_cents
        ):
            raise ValidationError(
                _("A soma das cotas deve ser igual ao total da cobrança."),
            )
        return cleaned_data

    @property
    def shares_by_participation(self) -> dict[int, int]:
        shares = {}
        for participation in self.participations:
            amount = self.cleaned_data.get(self.field_name(participation.pk))
            if amount is not None:
                shares[participation.pk] = int(amount * 100)
        return shares


class ChargeAllocationForm(forms.Form):
    """Editable, server-calculated shares before a charge exists."""

    def __init__(self, people, total_cents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.people = people
        self.total_cents = total_cents
        self.initial_shares = calculate_shares(
            total_cents,
            [user.pk for user in people],
        )
        for person in people:
            self.fields[f"share_{person.pk}"] = BrazilianDecimalField(
                label=person.name or person.username,
                max_digits=12,
                decimal_places=2,
                min_value=Decimal("0.00"),
                localize=True,
                initial=Decimal(self.initial_shares[person.pk]) / 100,
                widget=forms.TextInput(attrs={"inputmode": "decimal"}),
            )

    @property
    def shares_by_user(self):
        if not self.is_bound:
            return self.initial_shares
        return {
            person.pk: int(self.cleaned_data[f"share_{person.pk}"] * 100)
            for person in self.people
            if f"share_{person.pk}" in self.cleaned_data
        }

    def clean(self):
        cleaned_data = super().clean()
        shares = self.shares_by_user
        if len(shares) == len(self.people) and sum(shares.values()) != self.total_cents:
            raise ValidationError(
                _("A soma das cotas deve ser igual ao total da cobrança."),
            )
        return cleaned_data


class AcceptParticipationForm(forms.Form):
    expected_share_cents = forms.IntegerField(min_value=0)
    expected_creditor_id = forms.IntegerField(min_value=1)

    def validated_terms(self):
        if not self.is_valid():
            raise ValidationError(
                _("Confira a cota e o recebedor no convite antes de aceitar."),
            )
        return self.cleaned_data


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
            .exclude(pk__in=current_user_ids)
            .order_by("username")
        )


class ChargeAbsoluteDeleteForm(forms.Form):
    reason = forms.CharField(
        label=_("Motivo (opcional)"),
        required=False,
        max_length=CHARGE_CANCELLATION_REASON_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ChargeCancellationForm(forms.Form):
    reason = forms.CharField(
        label=_("Motivo do cancelamento (opcional)"),
        required=False,
        max_length=CHARGE_CANCELLATION_REASON_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
