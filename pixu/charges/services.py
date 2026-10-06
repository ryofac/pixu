from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import unicodedata
from datetime import timedelta
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.accounts.models import User
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment
from pixu.settlements.models import PendingReceiptDeletion
from pixu.settlements.tasks import delete_pending_receipt

from .models import CHARGE_CANCELLATION_REASON_MAX_LENGTH
from .models import CHARGE_DESCRIPTION_MAX_LENGTH
from .models import CHARGE_TITLE_MAX_LENGTH
from .models import MAX_GUEST_TOTAL_PARTICIPANTS
from .models import Charge
from .models import ChargeItem
from .models import ChargeDeletionAudit
from .models import Debt
from .models import Participation

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping


def calculate_shares(
    total_cents: int,
    participant_ids: Iterable[int],
    *,
    participant_count: int | None = None,
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
    if participant_count is None:
        participant_count = len(ordered_ids)
    if (
        isinstance(participant_count, bool)
        or not isinstance(participant_count, int)
        or participant_count < len(ordered_ids)
        or participant_count <= 0
    ):
        raise ValidationError({"participants": _("O total de participantes é inválido.")})
    base, remainder = divmod(total_cents, participant_count)
    return {
        user_id: base + (index < remainder) for index, user_id in enumerate(ordered_ids)
    }


def normalize_guest_name(value: str) -> str:
    """Normalize only for validation/search; the displayed name is preserved."""
    if not isinstance(value, str):
        raise ValidationError({"name": _("Informe um nome válido.")})
    normalized = " ".join(value.split()).strip()
    if not normalized or len(normalized) > 120:
        raise ValidationError({"name": _("Informe um nome entre 1 e 120 caracteres.")})
    return unicodedata.normalize("NFKC", normalized).casefold()


def _digest_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _new_guest_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def calculate_itemized_shares(
    total_cents: int,
    participation_ids,
    items=None,
    *,
    participant_count: int | None = None,
) -> dict[int, dict[str, int]]:
    """Return deterministic integer base/item/final shares for participation IDs."""
    if not isinstance(total_cents, int) or isinstance(total_cents, bool) or total_cents <= 0:
        raise ValidationError({"total_cents": _("Informe um valor total positivo em centavos.")})
    ids = sorted({int(value) for value in participation_ids})
    if not ids:
        return {}
    if participant_count is None:
        participant_count = len(ids)
    if (
        isinstance(participant_count, bool)
        or not isinstance(participant_count, int)
        or participant_count < len(ids)
        or participant_count <= 0
    ):
        raise ValidationError({"participants": _("O total de participantes é inválido.")})
    item_totals = {participation_id: 0 for participation_id in ids}
    for item in items or []:
        amount = item.amount_cents if hasattr(item, "amount_cents") else item["amount_cents"]
        owner = item.participation_id if hasattr(item, "participation_id") else item.get("participation_id")
        if owner not in item_totals:
            raise ValidationError({"items": _("Cada item precisa de uma pessoa do rateio.")})
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValidationError({"items": _("Os itens devem ter valor positivo em centavos.")})
        item_totals[owner] += amount
    extras = sum(item_totals.values())
    if extras > total_cents:
        raise ValidationError({"items": _("A soma dos itens não pode exceder o total.")})
    base_total, remainder = divmod(total_cents - extras, participant_count)
    result = {}
    for index, participation_id in enumerate(ids):
        base_share = base_total + (1 if index < remainder else 0)
        result[participation_id] = {
            "base_cents": base_share,
            "items_cents": item_totals[participation_id],
            "share_cents": base_share + item_totals[participation_id],
        }
    return result


def _recalculate_charge_shares(charge: Charge) -> list[Participation]:
    participations = list(
        charge.participations.select_for_update()
        .filter(state__in=(Participation.State.PENDING, Participation.State.ACCEPTED))
        .order_by("pk"),
    )
    values = calculate_itemized_shares(
        charge.total_cents,
        [participation.pk for participation in participations],
        charge.items.all(),
        participant_count=charge.guest_total_participants,
    )
    for participation in participations:
        calculated = values[participation.pk]
        participation.base_share_cents = calculated["base_cents"]
        participation.share_cents = calculated["share_cents"]
        participation.save(update_fields=["base_share_cents", "share_cents"])
        if participation.state == Participation.State.ACCEPTED:
            Debt.objects.filter(participation=participation).update(
                original_cents=participation.share_cents,
            )
            if participation.user_id == charge.creator_id:
                _sync_creator_debt(charge)
    return participations


@dataclass(frozen=True)
class GuestAccess:
    participation: Participation
    code: str


def cancel_charge(*, charge_id: int, actor: User, reason: str = "") -> Charge:
    """Cancel a charge while retaining its financial and receipt history."""
    if not isinstance(reason, str):
        raise ValidationError({"reason": _("Informe um motivo válido.")})
    reason = reason.strip()
    if len(reason) > CHARGE_CANCELLATION_REASON_MAX_LENGTH:
        raise ValidationError(
            {
                "reason": _(
                    "O motivo deve ter até %(limit)s caracteres.",
                )
                % {"limit": CHARGE_CANCELLATION_REASON_MAX_LENGTH},
            },
        )

    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        if charge.state == Charge.State.CANCELLED:
            return charge
        if charge.state not in {
            Charge.State.ACTIVE,
            Charge.State.AWAITING_ACCEPTANCE,
        }:
            raise ValidationError(_("Esta cobrança não pode ser cancelada."))

        charge_debts = Debt.objects.filter(participation__charge=charge)
        if Compensation.objects.filter(
            Q(debt__in=charge_debts) | Q(reciprocal_debt__in=charge_debts),
        ).exists():
            raise ValidationError(
                _(
                    "Esta cobrança possui uma compensação e não pode ser cancelada.",
                ),
            )

        cancelled_at = timezone.now()
        Participation.objects.filter(
            charge=charge,
            state=Participation.State.PENDING,
        ).update(state=Participation.State.CANCELLED)
        Participation.objects.filter(charge=charge, guest_access_digest__gt="").update(
            guest_access_digest="",
            guest_access_expires_at=cancelled_at,
        )
        Payment.objects.filter(debt__participation__charge=charge).update(
            state=Payment.State.REVOKED,
        )

        charge.state = Charge.State.CANCELLED
        charge.guest_entries_open = False
        charge.guest_entry_token_revoked_at = cancelled_at
        charge.cancelled_by = actor
        charge.cancelled_at = cancelled_at
        charge.cancellation_reason = reason
        charge.save(
            update_fields=[
                "state",
                "cancelled_by",
                "cancelled_at",
                "cancellation_reason",
                "guest_entries_open",
                "guest_entry_token_revoked_at",
            ],
        )
        return charge


def absolutely_delete_charge(
    *,
    charge_id: int,
    actor: User,
    reason: str = "",
) -> ChargeDeletionAudit:
    """Delete all charge records and enqueue private receipts for cleanup."""
    if not getattr(actor, "is_superuser", False):
        raise PermissionDenied
    if not isinstance(reason, str):
        raise ValidationError({"reason": _("Informe um motivo válido.")})
    reason = reason.strip()
    if len(reason) > CHARGE_CANCELLATION_REASON_MAX_LENGTH:
        raise ValidationError(
            {
                "reason": _("O motivo deve ter até %(limit)s caracteres.")
                % {"limit": CHARGE_CANCELLATION_REASON_MAX_LENGTH},
            },
        )

    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        charge_debts = Debt.objects.filter(participation__charge=charge)
        if Compensation.objects.filter(
            Q(debt__in=charge_debts) | Q(reciprocal_debt__in=charge_debts),
        ).exists():
            raise ValidationError(
                _(
                    "Esta cobrança possui uma compensação e não pode ser excluída.",
                ),
            )

        payments = list(
            Payment.objects.select_for_update()
            .filter(debt__participation__charge=charge)
            .order_by("pk"),
        )
        cleanup_ids = []
        for payment in payments:
            if not payment.receipt:
                continue
            pending, _created = PendingReceiptDeletion.objects.get_or_create(
                storage_alias="default",
                file_name=payment.receipt.name,
            )
            cleanup_ids.append(pending.pk)

        audit = ChargeDeletionAudit.objects.create(
            charge_id_snapshot=charge.pk,
            deleted_by=actor,
            reason=reason,
        )
        Payment.objects.filter(pk__in=[payment.pk for payment in payments]).delete()
        charge_debts.delete()
        charge.participations.all().delete()
        charge.delete()

        if cleanup_ids:
            transaction.on_commit(
                lambda ids=tuple(cleanup_ids): _enqueue_receipt_cleanup(ids),
            )
        return audit


def _enqueue_receipt_cleanup(pending_ids: tuple[int, ...]) -> None:
    for pending_id in pending_ids:
        try:
            delete_pending_receipt.delay(pending_id)
        except Exception:
            # Keep the outbox row durable; the retry management command can
            # enqueue it again after the broker becomes available.
            logger.exception(
                "Could not queue private receipt deletion %s",
                pending_id,
            )


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
    guest_invites_enabled: bool = False,
    guest_total_participants: int | None = None,
    guest_entry_limit: int = 10,
    guest_access_ttl_days: int = 7,
    items: Iterable[Mapping[str, object]] | None = None,
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
    if (
        isinstance(guest_entry_limit, bool)
        or not isinstance(guest_entry_limit, int)
        or not 1 <= guest_entry_limit <= 100
    ):
        raise ValidationError({"guest_entry_limit": _("O limite deve ficar entre 1 e 100.")})
    if (
        isinstance(guest_access_ttl_days, bool)
        or not isinstance(guest_access_ttl_days, int)
        or not 1 <= guest_access_ttl_days <= 30
    ):
        raise ValidationError({"guest_access_ttl_days": _("A validade deve ficar entre 1 e 30 dias.")})
    all_user_ids = ([creator.pk] if include_creator else []) + invitee_ids
    if guest_total_participants is not None and (
        isinstance(guest_total_participants, bool)
        or not isinstance(guest_total_participants, int)
        or not 1 <= guest_total_participants <= MAX_GUEST_TOTAL_PARTICIPANTS
    ):
        raise ValidationError(
            {"guest_total_participants": _("O total deve ficar entre 1 e 100 pessoas.")},
        )
    if guest_invites_enabled and guest_total_participants is not None and (
        guest_total_participants < len(all_user_ids)
    ):
        raise ValidationError(
            {
                "guest_total_participants": _(
                    "O total não pode ser menor que as pessoas já selecionadas.",
                ),
            },
        )
    if not all_user_ids and not guest_invites_enabled:
        raise ValidationError({"participants": _("Inclua ao menos uma pessoa no rateio.")})
    shares = calculate_shares(total_cents, all_user_ids) if all_user_ids else {}
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
            state=Charge.State.AWAITING_ACCEPTANCE
            if guest_invites_enabled or invitee_ids
            else Charge.State.ACTIVE,
            guest_invites_enabled=guest_invites_enabled,
            guest_total_participants=guest_total_participants,
            guest_entry_limit=guest_entry_limit,
            guest_access_ttl_days=guest_access_ttl_days,
            guest_entries_open=guest_invites_enabled,
        )
        if include_creator:
            creator_participation = Participation.objects.create(
                charge=charge,
                user=creator,
                share_cents=shares[creator.pk],
                base_share_cents=shares[creator.pk],
                state=Participation.State.ACCEPTED,
                accepted_at=timezone.now(),
            )
            _sync_creator_debt(charge)
        else:
            creator_participation = None
        created_invitees = Participation.objects.bulk_create(
            [
                Participation(
                    charge=charge,
                    user=invitees[user_id],
                    share_cents=shares[user_id],
                    base_share_cents=shares[user_id],
                    state=Participation.State.PENDING,
                )
                for user_id in sorted(invitee_ids)
            ],
        )
        if items:
            participants_by_user = {
                participation.user_id: participation
                for participation in [creator_participation, *created_invitees]
                if participation is not None
            }
            for item in items:
                try:
                    owner_id = int(item["user_id"])
                    description = str(item["description"]).strip()
                    amount_cents = int(item["amount_cents"])
                except (KeyError, TypeError, ValueError) as error:
                    raise ValidationError({"items": _("Revise os itens enviados.")}) from error
                owner = participants_by_user.get(owner_id)
                if owner is None:
                    raise ValidationError({"items": _("Cada item precisa de uma pessoa do rateio.")})
                ChargeItem.objects.create(
                    charge=charge,
                    participation=owner,
                    description=description,
                    amount_cents=amount_cents,
                )
        if items or guest_total_participants is not None:
            _recalculate_charge_shares(charge)
        if guest_invites_enabled:
            credentials = _rotate_guest_invite_locked(charge)
            charge._guest_credentials = credentials
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
        if charge.state == Charge.State.CANCELLED:
            raise ValidationError(_("Esta cobrança foi cancelada."))
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
                participation.base_share_cents = new_share if not charge.items.exists() else participation.base_share_cents
                participation.save(update_fields=["share_cents", "base_share_cents"])
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
    if charge.guest_invites_enabled and charge.guest_entries_open and charge.guest_total_participants is None:
        return
    participations = list(
        Participation.objects.select_for_update()
        .filter(charge=charge)
        .filter(state__in=(Participation.State.PENDING, Participation.State.ACCEPTED)),
    )
    if not participations:
        return
    if charge.guest_total_participants is not None:
        if not any(
            participation.state == Participation.State.ACCEPTED
            for participation in participations
        ):
            return
        if charge.state != Charge.State.ACTIVE:
            charge.state = Charge.State.ACTIVE
            charge.save(update_fields=["state"])
        return
    if any(
        participation.state != Participation.State.ACCEPTED
        for participation in participations
    ):
        return
    if charge.guest_total_participants is None and (
        sum(participation.share_cents for participation in participations)
        != charge.total_cents
    ):
        return
    if charge.state != Charge.State.ACTIVE:
        charge.state = Charge.State.ACTIVE
        charge.save(update_fields=["state"])


def _rotate_guest_invite_locked(charge: Charge) -> dict[str, str]:
    token = _new_guest_secret()
    code = secrets.token_hex(5).upper()
    now = timezone.now()
    charge.guest_entry_token_digest = _digest_secret(token)
    charge.guest_entry_code_digest = _digest_secret(code)
    charge.guest_entry_token_created_at = now
    charge.guest_entry_token_revoked_at = None
    charge.save(
        update_fields=[
            "guest_entry_token_digest",
            "guest_entry_code_digest",
            "guest_entry_token_created_at",
            "guest_entry_token_revoked_at",
        ],
    )
    return {"token": token, "code": code}


def rotate_guest_invite(*, charge_id: int, actor: User) -> dict[str, str]:
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        if not charge.guest_invites_enabled or charge.state == Charge.State.CANCELLED:
            raise ValidationError(_("Esta cobrança não aceita entradas anônimas."))
        return _rotate_guest_invite_locked(charge)


def revoke_guest_invite(*, charge_id: int, actor: User) -> Charge:
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        charge.guest_entry_token_revoked_at = timezone.now()
        charge.guest_entries_open = False
        charge.save(update_fields=["guest_entry_token_revoked_at", "guest_entries_open"])
        return charge


def _valid_shared_guest_secret(charge: Charge, secret: str) -> bool:
    if not charge.guest_invites_enabled or not charge.guest_entries_open:
        return False
    if charge.state == Charge.State.CANCELLED or charge.guest_entry_token_revoked_at:
        return False
    digest = _digest_secret(secret)
    return hmac.compare_digest(digest, charge.guest_entry_token_digest) or hmac.compare_digest(
        digest,
        charge.guest_entry_code_digest,
    )


def validate_guest_entry_link(*, charge_id: int, shared_secret: str) -> Charge:
    charge = Charge.objects.select_related("creator", "creditor").get(pk=charge_id)
    if not _valid_shared_guest_secret(charge, shared_secret):
        raise PermissionDenied
    return charge


def _guest_access_expiry(charge: Charge, created_at):
    expiry = created_at + timedelta(days=charge.guest_access_ttl_days)
    if charge.guest_entries_closed_at:
        expiry = max(
            expiry,
            charge.guest_entries_closed_at + timedelta(days=charge.guest_access_ttl_days),
        )
    return expiry


def enter_guest_charge(
    *,
    charge_id: int,
    shared_secret: str,
    name: str,
    account_user: User | None = None,
) -> GuestAccess:
    """Create one anonymous identity and return its one-time personal code."""
    normalized = normalize_guest_name(name)
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if not _valid_shared_guest_secret(charge, shared_secret):
            raise PermissionDenied
        active_guest_count = charge.participations.filter(
            guest_access_digest__gt="",
            state__in=(Participation.State.PENDING, Participation.State.ACCEPTED),
        ).count()
        if active_guest_count >= charge.guest_entry_limit:
            raise ValidationError(_("O limite de entradas desta cobrança foi atingido."))
        active_count = charge.participations.filter(
            state__in=(Participation.State.PENDING, Participation.State.ACCEPTED),
        ).count()
        if charge.guest_total_participants is not None and active_count >= charge.guest_total_participants:
            raise ValidationError(_("O total de participantes desta cobrança já foi preenchido."))
        if account_user is not None and charge.participations.filter(
            user=account_user,
            state__in=(Participation.State.PENDING, Participation.State.ACCEPTED),
        ).exists():
            raise ValidationError(_("Sua conta já participa desta cobrança."))
        now = timezone.now()
        code = secrets.token_hex(5).upper()
        participation = Participation.objects.create(
            charge=charge,
            user=account_user,
            guest_name=None if account_user is not None else " ".join(name.split()).strip(),
            guest_name_normalized=None if account_user is not None else normalized,
            guest_access_digest=_digest_secret(code),
            guest_access_created_at=now,
            guest_access_expires_at=_guest_access_expiry(charge, now),
            guest_claimed_at=now,
            state=Participation.State.PENDING,
            share_cents=0,
            base_share_cents=0,
        )
        _recalculate_charge_shares(charge)
        participation.refresh_from_db()
        return GuestAccess(participation=participation, code=code)


def get_guest_participation(*, participation_id: int, personal_code: str) -> Participation:
    try:
        participation = Participation.objects.select_related("charge", "charge__creditor").get(
            pk=participation_id,
            guest_access_digest__gt="",
        )
    except Participation.DoesNotExist as error:
        raise PermissionDenied from error
    charge = participation.charge
    if charge.state == Charge.State.CANCELLED:
        raise PermissionDenied
    if not participation.guest_access_digest or participation.guest_access_expires_at is None:
        raise PermissionDenied
    if participation.guest_access_expires_at < timezone.now():
        raise PermissionDenied
    if not hmac.compare_digest(
        _digest_secret(personal_code.strip().upper()),
        participation.guest_access_digest,
    ):
        raise PermissionDenied
    return participation


def confirm_guest_participation(
    *,
    participation_id: int,
    personal_code: str,
    expected_share_cents: int | None = None,
    expected_creditor_id: int | None = None,
) -> Participation:
    with transaction.atomic():
        stub = Participation.objects.only("charge_id").get(pk=participation_id)
        charge = Charge.objects.select_for_update().get(pk=stub.charge_id)
        participation = Participation.objects.select_for_update().get(
            pk=participation_id,
            charge=charge,
        )
        get_guest_participation(participation_id=participation_id, personal_code=personal_code)
        if charge.guest_entries_open and charge.guest_total_participants is None:
            raise ValidationError(_("O criador ainda precisa fechar as entradas antes da confirmação."))
        if participation.state == Participation.State.ACCEPTED:
            return participation
        if participation.state != Participation.State.PENDING:
            raise ValidationError(_("Esta entrada não está mais pendente."))
        if expected_share_cents is not None and expected_share_cents != participation.share_cents:
            raise ValidationError(_("A cota mudou. Confira o valor antes de confirmar."))
        if expected_creditor_id is not None and expected_creditor_id != charge.creditor_id:
            raise ValidationError(_("O recebedor mudou. Confira os dados antes de confirmar."))
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


def leave_guest_participation(*, participation_id: int, personal_code: str) -> Participation:
    with transaction.atomic():
        participation = get_guest_participation(
            participation_id=participation_id,
            personal_code=personal_code,
        )
        charge = Charge.objects.select_for_update().get(pk=participation.charge_id)
        participation = Participation.objects.select_for_update().get(pk=participation_id)
        if not charge.guest_entries_open:
            raise ValidationError(_("As entradas já foram fechadas."))
        if participation.state != Participation.State.PENDING:
            raise ValidationError(_("Esta participação já foi confirmada e não pode sair do rateio."))
        if Debt.objects.filter(participation=participation).exists():
            raise ValidationError(_("Esta participação já possui uma dívida."))
        participation.state = Participation.State.CANCELLED
        participation.guest_access_digest = ""
        participation.save(update_fields=["state", "guest_access_digest"])
        _recalculate_charge_shares(charge)
        return participation


def close_guest_entries(*, charge_id: int, actor: User) -> Charge:
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        if not charge.guest_invites_enabled:
            raise ValidationError(_("Esta cobrança não possui entradas anônimas."))
        active_count = charge.participations.filter(
            guest_access_digest__gt="",
            state__in=(Participation.State.PENDING, Participation.State.ACCEPTED),
        ).count()
        if active_count == 0:
            raise ValidationError(_("Inclua pelo menos uma pessoa antes de fechar as entradas."))
        charge.guest_entries_open = False
        charge.guest_entries_closed_at = timezone.now()
        charge.guest_entry_token_revoked_at = charge.guest_entries_closed_at
        charge.save(
            update_fields=[
                "guest_entries_open",
                "guest_entries_closed_at",
                "guest_entry_token_revoked_at",
            ],
        )
        for participation in charge.participations.filter(guest_access_digest__gt="").exclude(
            state=Participation.State.CANCELLED,
        ):
            participation.guest_access_expires_at = _guest_access_expiry(
                charge,
                participation.guest_access_created_at or timezone.now(),
            )
            participation.save(update_fields=["guest_access_expires_at"])
        _activate_when_ready(charge)
        return charge


def reopen_guest_entries(*, charge_id: int, actor: User) -> Charge:
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        if not charge.guest_invites_enabled or charge.state == Charge.State.CANCELLED:
            raise ValidationError(_("Esta cobrança não pode reabrir entradas."))
        if Payment.objects.filter(debt__participation__charge=charge).exists():
            raise ValidationError(_("Não é possível reabrir depois de um pagamento."))
        charge.guest_entries_open = True
        charge.guest_entries_closed_at = None
        charge.state = Charge.State.AWAITING_ACCEPTANCE
        charge.save(update_fields=["guest_entries_open", "guest_entries_closed_at", "state"])
        _rotate_guest_invite_locked(charge)
        _recalculate_charge_shares(charge)
        return charge


def add_charge_item(
    *,
    charge_id: int,
    actor: User,
    description: str,
    amount_cents: int,
    participation_id: int,
) -> ChargeItem:
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        _ensure_charge_editable(charge)
        if charge.locked_at is not None:
            raise ValidationError(_("Itens não podem mudar depois de um pagamento."))
        description = " ".join(str(description).split()).strip()
        if not description or len(description) > ChargeItem.DESCRIPTION_MAX_LENGTH:
            raise ValidationError({"description": _("Informe uma descrição de item válida.")})
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValidationError({"amount": _("O item deve ter valor positivo em centavos.")})
        participation = Participation.objects.filter(
            pk=participation_id,
            charge=charge,
            state__in=(Participation.State.PENDING, Participation.State.ACCEPTED),
        ).first()
        if participation is None:
            raise ValidationError({"participation": _("Escolha uma pessoa desta cobrança.")})
        item = ChargeItem.objects.create(
            charge=charge,
            participation=participation,
            description=description,
            amount_cents=amount_cents,
        )
        _recalculate_charge_shares(charge)
        return item


def remove_charge_item(*, item_id: int, actor: User) -> None:
    with transaction.atomic():
        item = ChargeItem.objects.select_related("charge").select_for_update().get(pk=item_id)
        charge = Charge.objects.select_for_update().get(pk=item.charge_id)
        if charge.creator_id != actor.pk:
            raise PermissionDenied
        _ensure_charge_editable(charge)
        if charge.locked_at is not None:
            raise ValidationError(_("Itens não podem mudar depois de um pagamento."))
        item.delete()
        _recalculate_charge_shares(charge)


def _ensure_charge_editable(charge: Charge) -> None:
    if charge.state == Charge.State.CANCELLED:
        raise ValidationError(_("Esta cobrança foi cancelada e não pode ser editada."))
    if charge.locked_at is not None:
        raise ValidationError(
            _("Esta cobrança não pode mais ser editada após uma operação financeira."),
        )
