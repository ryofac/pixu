from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.accounts.models import User

from .models import Charge
from .models import Debt
from .models import Participation


def calculate_shares(total_cents: int, participant_ids: Iterable[int]) -> dict[int, int]:
    """Split integer cents evenly, assigning remainders by persistent user ID."""
    if isinstance(total_cents, bool) or not isinstance(total_cents, int) or total_cents <= 0:
        raise ValidationError({"total_cents": _("Informe um valor total positivo em centavos.")})

    ids = list(participant_ids)
    if not ids:
        raise ValidationError({"participants": _("Inclua ao menos uma pessoa no rateio.")})
    if any(isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0 for user_id in ids):
        raise ValidationError({"participants": _("A lista de participantes é inválida.")})
    if len(ids) != len(set(ids)):
        raise ValidationError({"participants": _("Uma pessoa não pode aparecer mais de uma vez.")})

    ordered_ids = sorted(ids)
    base, remainder = divmod(total_cents, len(ordered_ids))
    return {
        user_id: base + (index < remainder)
        for index, user_id in enumerate(ordered_ids)
    }


def create_charge(
    *,
    creator: User,
    title: str,
    total_cents: int,
    invitee_ids: Iterable[int],
    description: str = "",
) -> Charge:
    """Create a charge, creator participation, and pending invitations atomically."""
    cleaned_title = title.strip()
    cleaned_description = description.strip()
    if not cleaned_title or len(cleaned_title) > 120:
        raise ValidationError({"title": _("Informe um título com até 120 caracteres.")})
    if len(cleaned_description) > 1000:
        raise ValidationError({"description": _("A descrição pode ter até 1000 caracteres.")})

    invitee_ids = list(invitee_ids)
    if creator.pk in invitee_ids:
        raise ValidationError({"invitee_ids": _("Você já participa automaticamente desta cobrança.")})
    if len(invitee_ids) != len(set(invitee_ids)):
        raise ValidationError({"invitee_ids": _("Uma pessoa não pode ser convidada mais de uma vez.")})

    invitees = User.objects.filter(pk__in=invitee_ids, is_active=True).in_bulk()
    if set(invitees) != set(invitee_ids):
        raise ValidationError({"invitee_ids": _("Selecione somente contas ativas já cadastradas.")})

    all_user_ids = [creator.pk, *invitee_ids]
    shares = calculate_shares(total_cents, all_user_ids)
    with transaction.atomic():
        charge = Charge.objects.create(
            creator=creator,
            title=cleaned_title,
            description=cleaned_description,
            total_cents=total_cents,
            state=(Charge.State.ACTIVE if not invitee_ids else Charge.State.AWAITING_ACCEPTANCE),
        )
        Participation.objects.create(
            charge=charge,
            user=creator,
            share_cents=shares[creator.pk],
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
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


def accept_participation(*, participation_id: int, actor: User) -> Participation:
    """Accept an invitation and create its debt once, under the charge lock."""
    with transaction.atomic():
        participation_stub = Participation.objects.only("charge_id").get(pk=participation_id)
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

        participation.state = Participation.State.ACCEPTED
        participation.accepted_at = timezone.now()
        participation.save(update_fields=["state", "accepted_at"])

        if participation.user_id != charge.creator_id:
            Debt.objects.get_or_create(
                participation=participation,
                defaults={
                    "debtor_id": participation.user_id,
                    "creditor_id": charge.creator_id,
                    "original_cents": participation.share_cents,
                },
            )
        _activate_when_ready(charge)
        return participation


def decline_participation(*, participation_id: int, actor: User) -> Participation:
    """Decline a pending invitation without creating a debt."""
    with transaction.atomic():
        participation_stub = Participation.objects.only("charge_id").get(pk=participation_id)
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
        participation_stub = Participation.objects.only("charge_id").get(pk=participation_id)
        charge = Charge.objects.select_for_update().get(pk=participation_stub.charge_id)
        declined = Participation.objects.select_for_update().get(
            pk=participation_id,
            charge=charge,
        )
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        _ensure_charge_editable(charge)
        if charge.state != Charge.State.AWAITING_ACCEPTANCE:
            raise ValidationError(_("Só é possível substituir convites antes da ativação."))
        if declined.state != Participation.State.DECLINED:
            raise ValidationError(_("Somente uma participação recusada pode ser substituída."))
        if replacement_user_id == declined.user_id:
            raise ValidationError(_("Escolha outra pessoa para substituir o convite recusado."))
        if replacement_user_id == charge.creator_id:
            raise ValidationError(_("O criador já participa automaticamente."))
        if Participation.objects.filter(charge=charge, user_id=replacement_user_id).exists():
            raise ValidationError(_("Essa pessoa já consta entre os participantes da cobrança."))
        try:
            replacement_user = User.objects.get(pk=replacement_user_id, is_active=True)
        except User.DoesNotExist as error:
            raise ValidationError(_("Selecione uma conta ativa já cadastrada.")) from error

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
) -> list[Participation]:
    """Edit the creator's and pending participants' shares before a financial event."""
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
        current_ids = {participation.pk for participation in participations}
        if set(shares_by_participation) != current_ids:
            raise ValidationError(_("Revise todas as cotas atuais antes de salvar."))
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in shares_by_participation.values()
        ):
            raise ValidationError(_("As cotas devem ser valores inteiros não negativos em centavos."))
        if sum(shares_by_participation.values()) != charge.total_cents:
            raise ValidationError(_("A soma das cotas deve ser igual ao total da cobrança."))

        for participation in participations:
            new_share = shares_by_participation[participation.pk]
            editable = (
                participation.user_id == charge.creator_id
                or participation.state == Participation.State.PENDING
            )
            if not editable and new_share != participation.share_cents:
                raise ValidationError(_("A cota de uma participação aceita não pode ser alterada."))

        for participation in participations:
            new_share = shares_by_participation[participation.pk]
            if new_share != participation.share_cents:
                participation.share_cents = new_share
                participation.save(update_fields=["share_cents"])
        return participations


def _activate_when_ready(charge: Charge) -> None:
    participations = list(
        Participation.objects.select_for_update()
        .filter(charge=charge)
        .exclude(state=Participation.State.DECLINED),
    )
    if any(participation.state != Participation.State.ACCEPTED for participation in participations):
        return
    if sum(participation.share_cents for participation in participations) != charge.total_cents:
        return
    if charge.state != Charge.State.ACTIVE:
        charge.state = Charge.State.ACTIVE
        charge.save(update_fields=["state"])


def _ensure_charge_editable(charge: Charge) -> None:
    if charge.locked_at is not None:
        raise ValidationError(_("Esta cobrança não pode mais ser editada após uma operação financeira."))
