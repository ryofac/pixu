from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.accounts.models import User

from .models import CHARGE_DESCRIPTION_MAX_LENGTH
from .models import CHARGE_TITLE_MAX_LENGTH
from .models import Charge
from .models import Debt
from .models import Participation

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping


def calculate_shares(
    total_cents: int,
    participant_ids: Iterable[int],
) -> dict[int, int]:
    """Split integer cents evenly, assigning remainders by persistent user ID."""
    if (
        isinstance(total_cents, bool)
        or not isinstance(total_cents, int)
        or total_cents <= 0
    ):
        raise ValidationError(
            {"total_cents": _("Informe um valor total positivo em centavos.")},
        )

    ids = list(participant_ids)
    if not ids:
        raise ValidationError(
            {"participants": _("Inclua ao menos uma pessoa no rateio.")},
        )
    if any(
        isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0
        for user_id in ids
    ):
        raise ValidationError(
            {"participants": _("A lista de participantes é inválida.")},
        )
    if len(ids) != len(set(ids)):
        raise ValidationError(
            {"participants": _("Uma pessoa não pode aparecer mais de uma vez.")},
        )

    ordered_ids = sorted(ids)
    base, remainder = divmod(total_cents, len(ordered_ids))
    return {
        user_id: base + (index < remainder) for index, user_id in enumerate(ordered_ids)
    }


def create_charge(  # noqa: PLR0913 - explicit keyword-only charge terms
    *,
    creator: User,
    title: str,
    total_cents: int,
    invitee_ids: Iterable[int],
    description: str = "",
    creditor_id: int | None = None,
    include_creator: bool = True,
    shares_by_user: Mapping[int, int] | None = None,
) -> Charge:
    """Create the selected shares, recipient, and invitations atomically."""
    cleaned_title = title.strip()
    cleaned_description = description.strip()
    if not cleaned_title or len(cleaned_title) > CHARGE_TITLE_MAX_LENGTH:
        raise ValidationError(
            {
                "title": _(
                    "Informe um título com até %s caracteres.",
                )
                % CHARGE_TITLE_MAX_LENGTH,
            },
        )
    if len(cleaned_description) > CHARGE_DESCRIPTION_MAX_LENGTH:
        raise ValidationError(
            {
                "description": _(
                    "A descrição pode ter até %s caracteres.",
                )
                % CHARGE_DESCRIPTION_MAX_LENGTH,
            },
        )

    invitee_ids = list(invitee_ids)
    if creator.pk in invitee_ids:
        raise ValidationError(
            {"invitee_ids": _("Use a opção de participação para incluir sua cota.")},
        )
    if len(invitee_ids) != len(set(invitee_ids)):
        raise ValidationError(
            {"invitee_ids": _("Uma pessoa não pode ser convidada mais de uma vez.")},
        )

    invitees = User.objects.filter(pk__in=invitee_ids, is_active=True).in_bulk()
    if set(invitees) != set(invitee_ids):
        raise ValidationError(
            {"invitee_ids": _("Selecione somente contas ativas já cadastradas.")},
        )

    creditor_id = creator.pk if creditor_id is None else creditor_id
    _validate_creditor(creditor_id)
    all_user_ids = ([creator.pk] if include_creator else []) + invitee_ids
    shares = calculate_shares(total_cents, all_user_ids)
    if shares_by_user is not None:
        _validate_shares(shares_by_user, all_user_ids, total_cents)
        shares = dict(shares_by_user)
    with transaction.atomic():
        charge = Charge.objects.create(
            creator=creator,
            creditor_id=creditor_id,
            title=cleaned_title,
            description=cleaned_description,
            total_cents=total_cents,
            state=(
                Charge.State.ACTIVE
                if not invitee_ids
                else Charge.State.AWAITING_ACCEPTANCE
            ),
        )
        if include_creator:
            Participation.objects.create(
                charge=charge,
                user=creator,
                share_cents=shares[creator.pk],
                state=Participation.State.ACCEPTED,
                accepted_at=timezone.now(),
            )
            _sync_creator_debt(charge)
        Participation.objects.bulk_create(
            [
                Participation(
                    charge=charge,
                    user=invitees[user_id],
                    share_cents=shares[user_id],
                    state=Participation.State.PENDING,
                )
                for user_id in sorted(invitee_ids)
            ],
        )
    return charge


def accept_participation(
    *,
    participation_id: int,
    actor: User,
    expected_share_cents: int | None = None,
    expected_creditor_id: int | None = None,
) -> Participation:
    """Accept an invitation and create its debt once, under the charge lock."""
    with transaction.atomic():
        participation_stub = Participation.objects.only("charge_id").get(
            pk=participation_id,
        )
        charge = Charge.objects.select_for_update().get(pk=participation_stub.charge_id)
        participation = Participation.objects.select_for_update().get(
            pk=participation_id,
            charge=charge,
        )
        if participation.user_id != actor.pk:
            raise PermissionDenied
        if participation.state == Participation.State.ACCEPTED:
            return participation
        if participation.state != Participation.State.PENDING:
            raise ValidationError(_("Este convite não está mais pendente."))
        if (
            expected_share_cents is not None
            and expected_share_cents != participation.share_cents
        ) or (
            expected_creditor_id is not None
            and expected_creditor_id != charge.creditor_id
        ):
            raise ValidationError(
                _("O rateio ou o recebedor mudou. Confira o convite antes de aceitar."),
            )

        participation.state = Participation.State.ACCEPTED
        participation.accepted_at = timezone.now()
        participation.save(update_fields=["state", "accepted_at"])

        if participation.user_id != charge.creditor_id:
            Debt.objects.get_or_create(
                participation=participation,
                defaults={
                    "debtor_id": participation.user_id,
                    "creditor_id": charge.creditor_id,
                    "original_cents": participation.share_cents,
                },
            )
        _activate_when_ready(charge)
        return participation


def decline_participation(*, participation_id: int, actor: User) -> Participation:
    """Decline a pending invitation without creating a debt."""
    with transaction.atomic():
        participation_stub = Participation.objects.only("charge_id").get(
            pk=participation_id,
        )
        charge = Charge.objects.select_for_update().get(pk=participation_stub.charge_id)
        participation = Participation.objects.select_for_update().get(
            pk=participation_id,
            charge=charge,
        )
        if participation.user_id != actor.pk:
            raise PermissionDenied
        if participation.state != Participation.State.PENDING:
            raise ValidationError(_("Somente convites pendentes podem ser recusados."))

        participation.state = Participation.State.DECLINED
        participation.declined_at = timezone.now()
        participation.save(update_fields=["state", "declined_at"])
        return participation


def replace_declined_participant(
    *,
    participation_id: int,
    replacement_user_id: int,
    actor: User,
) -> Participation:
    """Replace a declined invite while preserving the declined row as history."""
    with transaction.atomic():
        participation_stub = Participation.objects.only("charge_id").get(
            pk=participation_id,
        )
        charge = Charge.objects.select_for_update().get(pk=participation_stub.charge_id)
        declined = Participation.objects.select_for_update().get(
            pk=participation_id,
            charge=charge,
        )
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        _ensure_charge_editable(charge)
        if charge.state != Charge.State.AWAITING_ACCEPTANCE:
            raise ValidationError(
                _("Só é possível substituir convites antes da ativação."),
            )
        if declined.state != Participation.State.DECLINED:
            raise ValidationError(
                _("Somente uma participação recusada pode ser substituída."),
            )
        if replacement_user_id == declined.user_id:
            raise ValidationError(
                _("Escolha outra pessoa para substituir o convite recusado."),
            )
        if Participation.objects.filter(
            charge=charge,
            user_id=replacement_user_id,
        ).exists():
            raise ValidationError(
                _("Essa pessoa já consta entre os participantes da cobrança."),
            )
        try:
            replacement_user = User.objects.get(pk=replacement_user_id, is_active=True)
        except User.DoesNotExist as error:
            raise ValidationError(
                _("Selecione uma conta ativa já cadastrada."),
            ) from error

        return Participation.objects.create(
            charge=charge,
            user=replacement_user,
            share_cents=declined.share_cents,
            state=Participation.State.PENDING,
        )


def edit_participation_shares(
    *,
    charge_id: int,
    shares_by_participation: Mapping[int, int],
    actor: User,
    creditor_id: int | None = None,
) -> list[Participation]:
    """Edit allowed shares and the recipient under the same lock as acceptance."""
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        _ensure_charge_editable(charge)

        participations = list(
            Participation.objects.select_for_update()
            .filter(charge=charge)
            .exclude(state=Participation.State.DECLINED)
            .order_by("pk"),
        )
        _validate_shares(
            shares_by_participation,
            [participation.pk for participation in participations],
            charge.total_cents,
        )
        creditor_id = charge.creditor_id if creditor_id is None else creditor_id
        if creditor_id != charge.creditor_id:
            _validate_creditor(creditor_id)
        if creditor_id != charge.creditor_id and any(
            participation.user_id != charge.creator_id
            and participation.state == Participation.State.ACCEPTED
            for participation in participations
        ):
            raise ValidationError(
                _("O recebedor não pode mudar depois do aceite de outra pessoa."),
            )

        for participation in participations:
            new_share = shares_by_participation[participation.pk]
            editable = (
                participation.user_id == charge.creator_id
                or participation.state == Participation.State.PENDING
            )
            if not editable and new_share != participation.share_cents:
                raise ValidationError(
                    _("A cota de uma participação aceita não pode ser alterada."),
                )

        for participation in participations:
            new_share = shares_by_participation[participation.pk]
            if new_share != participation.share_cents:
                participation.share_cents = new_share
                participation.save(update_fields=["share_cents"])
        if creditor_id != charge.creditor_id:
            charge.creditor_id = creditor_id
            charge.save(update_fields=["creditor"])
        _sync_creator_debt(charge)
        _activate_when_ready(charge)
        return participations


def _validate_shares(shares, expected_ids, total_cents):
    if set(shares) != set(expected_ids):
        raise ValidationError(_("Revise todas as cotas atuais antes de salvar."))
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in shares.values()
    ):
        raise ValidationError(
            _("As cotas devem ser valores inteiros não negativos em centavos."),
        )
    if sum(shares.values()) != total_cents:
        raise ValidationError(
            _("A soma das cotas deve ser igual ao total da cobrança."),
        )


def _validate_creditor(creditor_id):
    if (
        isinstance(creditor_id, bool)
        or not isinstance(creditor_id, int)
        or not User.objects.filter(pk=creditor_id, is_active=True).exists()
    ):
        raise ValidationError(
            _("Selecione uma conta ativa para receber os pagamentos."),
        )


def _sync_creator_debt(charge):
    participation = charge.participations.filter(
        user_id=charge.creator_id,
        state=Participation.State.ACCEPTED,
    ).first()
    if participation is None:
        return
    if charge.creator_id == charge.creditor_id:
        Debt.objects.filter(participation=participation).delete()
    else:
        Debt.objects.update_or_create(
            participation=participation,
            defaults={
                "debtor_id": charge.creator_id,
                "creditor_id": charge.creditor_id,
                "original_cents": participation.share_cents,
            },
        )


def _activate_when_ready(charge: Charge) -> None:
    participations = list(
        Participation.objects.select_for_update()
        .filter(charge=charge)
        .exclude(state=Participation.State.DECLINED),
    )
    if any(
        participation.state != Participation.State.ACCEPTED
        for participation in participations
    ):
        return
    if (
        sum(participation.share_cents for participation in participations)
        != charge.total_cents
    ):
        return
    if charge.state != Charge.State.ACTIVE:
        charge.state = Charge.State.ACTIVE
        charge.save(update_fields=["state"])


def _ensure_charge_editable(charge: Charge) -> None:
    if charge.locked_at is not None:
        raise ValidationError(
            _("Esta cobrança não pode mais ser editada após uma operação financeira."),
        )
