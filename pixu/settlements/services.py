from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.models import Participation

from .models import PAYMENT_REFERENCE_MAX_LENGTH
from .models import Compensation
from .models import Payment
from .validators import validate_receipt


@dataclass(frozen=True)
class PaymentBalance:
    original_cents: int
    confirmed_cents: int
    compensated_cents: int
    pending_cents: int
    open_cents: int
    available_cents: int


@dataclass(frozen=True)
class CompensationOption:
    reciprocal_debt: Debt
    current_available_cents: int
    reciprocal_available_cents: int
    max_amount_cents: int


def payment_balance(debt: Debt | int) -> PaymentBalance:
    debt_id = debt.pk if isinstance(debt, Debt) else debt
    debt_value = Debt.objects.only("original_cents").get(pk=debt_id)
    totals = debt_value.payments.aggregate(
        confirmed=Coalesce(
            Sum("amount_cents", filter=Q(state=Payment.State.CONFIRMED)),
            0,
        ),
        pending=Coalesce(
            Sum("amount_cents", filter=Q(state=Payment.State.PENDING)),
            0,
        ),
    )
    compensated = Compensation.objects.filter(
        Q(debt_id=debt_id) | Q(reciprocal_debt_id=debt_id),
    ).aggregate(total=Coalesce(Sum("amount_cents"), 0))["total"]
    confirmed = int(totals["confirmed"] or 0)
    pending = int(totals["pending"] or 0)
    compensated = int(compensated or 0)
    original = int(debt_value.original_cents)
    open_cents = max(original - confirmed - compensated, 0)
    return PaymentBalance(
        original_cents=original,
        confirmed_cents=confirmed,
        compensated_cents=compensated,
        pending_cents=pending,
        open_cents=open_cents,
        available_cents=max(open_cents - pending, 0),
    )


def suggest_compensations(*, debt_id: int, actor) -> list[CompensationOption]:
    """Return available inverse debts for the authenticated debtor."""
    debt = Debt.objects.select_related("participation__charge").get(pk=debt_id)
    if debt.debtor_id != actor.pk:
        raise PermissionDenied
    if (
        debt.participation.charge.state != Charge.State.ACTIVE
        or debt.participation.state != Participation.State.ACCEPTED
    ):
        return []

    current_available = payment_balance(debt).available_cents
    if current_available <= 0:
        return []

    reciprocal_debts = (
        Debt.objects.filter(
            debtor_id=debt.creditor_id,
            creditor_id=debt.debtor_id,
            participation__state=Participation.State.ACCEPTED,
            participation__charge__state=Charge.State.ACTIVE,
        )
        .exclude(pk=debt.pk)
        .select_related("participation__charge", "debtor", "creditor")
        .order_by("-participation__charge__created_at", "-pk")
    )
    options = []
    for reciprocal_debt in reciprocal_debts:
        reciprocal_available = payment_balance(reciprocal_debt).available_cents
        max_amount = min(current_available, reciprocal_available)
        if max_amount > 0:
            options.append(
                CompensationOption(
                    reciprocal_debt=reciprocal_debt,
                    current_available_cents=current_available,
                    reciprocal_available_cents=reciprocal_available,
                    max_amount_cents=max_amount,
                ),
            )
    return options


def _lock_compensation_pair(
    debt_id: int,
    reciprocal_debt_id: int,
) -> tuple[Debt, Debt, Charge, Charge]:
    expected_debt_ids = {debt_id, reciprocal_debt_id}
    debt_refs = list(
        Debt.objects.filter(pk__in=expected_debt_ids).values(
            "pk",
            "participation__charge_id",
        ),
    )
    if {row["pk"] for row in debt_refs} != expected_debt_ids:
        raise Debt.DoesNotExist

    charge_id_by_debt = {
        row["pk"]: row["participation__charge_id"] for row in debt_refs
    }
    expected_charge_ids = set(charge_id_by_debt.values())
    charges = {
        charge.pk: charge
        for charge in Charge.objects.select_for_update()
        .filter(pk__in=expected_charge_ids)
        .order_by("pk")
    }
    debts = {
        debt.pk: debt
        for debt in Debt.objects.select_for_update()
        .filter(pk__in=expected_debt_ids)
        .order_by("pk")
    }
    if debts.keys() != expected_debt_ids or charges.keys() != expected_charge_ids:
        raise Debt.DoesNotExist

    return (
        debts[debt_id],
        debts[reciprocal_debt_id],
        charges[charge_id_by_debt[debt_id]],
        charges[charge_id_by_debt[reciprocal_debt_id]],
    )


def _validate_compensation_pair(
    debt: Debt,
    reciprocal_debt: Debt,
    actor,
    debt_charge: Charge,
    reciprocal_charge: Charge,
) -> None:
    if debt.debtor_id != actor.pk:
        raise PermissionDenied
    if (
        debt.debtor_id != reciprocal_debt.creditor_id
        or debt.creditor_id != reciprocal_debt.debtor_id
    ):
        raise ValidationError(
            {"reciprocal_debt": _("As dívidas selecionadas não são recíprocas.")},
        )

    participation_states = dict(
        Participation.objects.filter(
            pk__in=[debt.participation_id, reciprocal_debt.participation_id],
        ).values_list("pk", "state"),
    )
    if (
        debt_charge.state != Charge.State.ACTIVE
        or reciprocal_charge.state != Charge.State.ACTIVE
        or participation_states.get(debt.participation_id)
        != Participation.State.ACCEPTED
        or participation_states.get(reciprocal_debt.participation_id)
        != Participation.State.ACCEPTED
    ):
        raise ValidationError(
            _("Só é possível compensar dívidas aceitas de cobranças ativas."),
        )


def _validate_compensation_availability(
    debt: Debt,
    reciprocal_debt: Debt,
    amount_cents: int,
) -> None:
    available = min(
        payment_balance(debt).available_cents,
        payment_balance(reciprocal_debt).available_cents,
    )
    if amount_cents > available:
        raise ValidationError(
            {"amount": _("O valor excede o disponível em uma das dívidas.")},
        )


def _lock_charges_after_compensation(
    debt_charge: Charge,
    reciprocal_charge: Charge,
) -> None:
    now = timezone.now()
    unique_charges = {
        debt_charge.pk: debt_charge,
        reciprocal_charge.pk: reciprocal_charge,
    }
    for charge in unique_charges.values():
        if charge.locked_at is None:
            charge.locked_at = now
            charge.save(update_fields=["locked_at"])


def _validate_compensation_request(amount_cents: int, request_id: UUID | str) -> UUID:
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
        raise ValidationError({"amount": _("Informe um valor válido em centavos.")})
    if amount_cents <= 0:
        raise ValidationError(
            {"amount": _("O valor da compensação deve ser positivo.")},
        )
    if isinstance(request_id, UUID):
        return request_id
    try:
        return UUID(str(request_id))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValidationError(
            {"request_id": _("A identificação da solicitação é inválida.")},
        ) from error


def apply_compensation(
    *,
    debt_id: int,
    reciprocal_debt_id: int,
    actor,
    amount_cents: int,
    request_id: UUID | str,
) -> Compensation:
    """Apply an accepted reciprocal debt reduction atomically and idempotently."""
    request_id = _validate_compensation_request(amount_cents, request_id)

    def get_repeated_request() -> Compensation | None:
        try:
            existing = Compensation.objects.get(request_id=request_id)
        except Compensation.DoesNotExist:
            return None
        if (
            existing.debt_id != debt_id
            or existing.reciprocal_debt_id != reciprocal_debt_id
            or existing.initiated_by_id != actor.pk
            or existing.amount_cents != amount_cents
        ):
            raise ValidationError(
                {
                    "request_id": _(
                        "Esta identificação já foi usada por outra solicitação.",
                    ),
                },
            )
        return existing

    try:
        with transaction.atomic():
            if debt_id == reciprocal_debt_id:
                raise ValidationError(
                    {
                        "reciprocal_debt": _(
                            "Escolha uma dívida diferente para compensar.",
                        ),
                    },
                )
            (
                debt,
                reciprocal_debt,
                debt_charge,
                reciprocal_charge,
            ) = _lock_compensation_pair(debt_id, reciprocal_debt_id)

            repeated = get_repeated_request()
            if repeated is not None:
                return repeated

            _validate_compensation_pair(
                debt,
                reciprocal_debt,
                actor,
                debt_charge,
                reciprocal_charge,
            )
            _validate_compensation_availability(
                debt,
                reciprocal_debt,
                amount_cents,
            )

            compensation = Compensation.objects.create(
                debt=debt,
                reciprocal_debt=reciprocal_debt,
                initiated_by=actor,
                amount_cents=amount_cents,
                request_id=request_id,
            )
            _lock_charges_after_compensation(debt_charge, reciprocal_charge)
            return compensation
    except IntegrityError:
        repeated = get_repeated_request()
        if repeated is not None:
            return repeated
        raise


def _lock_payment_context(payment_id: int):
    payment_stub = Payment.objects.select_related("debt__participation").get(
        pk=payment_id,
    )
    charge = Charge.objects.select_for_update().get(
        pk=payment_stub.debt.participation.charge_id,
    )
    debt = Debt.objects.select_for_update().get(pk=payment_stub.debt_id)
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    return payment, debt, charge


def record_payment(
    *,
    debt_id: int,
    actor=None,
    amount_cents: int,
    reference: str = "",
    receipt=None,
    guest_participation_id: int | None = None,
    guest_code: str | None = None,
) -> Payment:
    """Reserve a partial payment and lock its charge atomically."""
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
        raise ValidationError({"amount": _("Informe um valor válido em centavos.")})
    if amount_cents <= 0:
        raise ValidationError({"amount": _("O pagamento deve ser positivo.")})
    reference = reference.strip()
    if len(reference) > PAYMENT_REFERENCE_MAX_LENGTH:
        raise ValidationError(
            {"reference": _("A referência deve ter até 500 caracteres.")},
        )
    with transaction.atomic():
        debt_stub = Debt.objects.select_related("participation").get(pk=debt_id)
        charge = Charge.objects.select_for_update().get(
            pk=debt_stub.participation.charge_id,
        )
        debt = Debt.objects.select_for_update().get(pk=debt_id)
        if guest_participation_id is not None:
            from pixu.charges.services import get_guest_participation

            if guest_code is None or guest_participation_id != debt.participation_id:
                raise PermissionDenied
            guest_participation = get_guest_participation(
                participation_id=guest_participation_id,
                personal_code=guest_code,
            )
            if guest_participation.state != Participation.State.ACCEPTED:
                raise ValidationError(_("Confirme sua cota antes de registrar o pagamento."))
            payer_id = guest_participation.user_id
        else:
            if actor is None or debt.debtor_id != actor.pk:
                raise PermissionDenied
            payer_id = debt.debtor_id
        if charge.state != Charge.State.ACTIVE:
            raise ValidationError(_("Só é possível pagar uma cobrança ativa."))
        balance = payment_balance(debt)
        if amount_cents > balance.available_cents:
            raise ValidationError(
                {"amount": _("O valor excede o disponível para esta dívida.")},
            )
        receipt_data = validate_receipt(receipt) if receipt else None
        payment = Payment(
            debt=debt,
            payer_id=payer_id,
            creditor_id=debt.creditor_id,
            amount_cents=amount_cents,
            reference=reference,
            state=Payment.State.PENDING,
        )
        if receipt_data:
            payment.receipt = receipt
            payment.receipt_original_name = receipt_data.original_name
            payment.receipt_content_type = receipt_data.content_type
            payment.receipt_size = receipt_data.size
        payment.save()
        if charge.locked_at is None:
            charge.locked_at = timezone.now()
            charge.save(update_fields=["locked_at"])
        return payment


def confirm_payment(*, payment_id: int, actor) -> Payment:
    with transaction.atomic():
        payment, debt, _charge = _lock_payment_context(payment_id)
        if debt.creditor_id != actor.pk:
            raise PermissionDenied
        if payment.state == Payment.State.CONFIRMED:
            return payment
        if payment.state != Payment.State.PENDING:
            raise ValidationError(_("Este pagamento não está mais pendente."))
        payment.state = Payment.State.CONFIRMED
        payment.confirmed_by = actor
        payment.confirmed_at = timezone.now()
        payment.save(update_fields=["state", "confirmed_by", "confirmed_at"])
        if debt.debtor_id is None and payment_balance(debt).open_cents <= 0:
            participation = debt.participation
            participation.guest_access_digest = ""
            participation.guest_access_expires_at = timezone.now()
            participation.save(update_fields=["guest_access_digest", "guest_access_expires_at"])
        return payment


def reject_payment(*, payment_id: int, actor) -> Payment:
    with transaction.atomic():
        payment, debt, _charge = _lock_payment_context(payment_id)
        if debt.creditor_id != actor.pk:
            raise PermissionDenied
        if payment.state == Payment.State.REJECTED:
            return payment
        if payment.state != Payment.State.PENDING:
            raise ValidationError(_("Este pagamento não está mais pendente."))
        payment.state = Payment.State.REJECTED
        payment.rejected_by = actor
        payment.rejected_at = timezone.now()
        payment.save(update_fields=["state", "rejected_by", "rejected_at"])
        return payment


def _lock_receipt_payment(payment_id: int, actor):
    payment_stub = Payment.objects.select_related("debt__participation").get(
        pk=payment_id,
    )
    _charge = Charge.objects.select_for_update().get(
        pk=payment_stub.debt.participation.charge_id,
    )
    debt = Debt.objects.select_for_update().get(pk=payment_stub.debt_id)
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    if debt.debtor_id != actor.pk:
        raise PermissionDenied
    if payment.state != Payment.State.PENDING:
        raise ValidationError(
            _("O comprovante só pode ser alterado enquanto o pagamento está pendente."),
        )
    return payment, debt


def replace_receipt(*, payment_id: int, actor, receipt) -> Payment:
    """Replace a pending payment receipt without touching its financial state."""
    receipt_data = validate_receipt(receipt)
    with transaction.atomic():
        payment, _debt = _lock_receipt_payment(payment_id, actor)
        old_name = payment.receipt.name if payment.receipt else ""
        old_storage = payment.receipt.storage if payment.receipt else None
        payment.receipt.save(receipt.name, receipt, save=False)
        new_name = payment.receipt.name
        payment.receipt_original_name = receipt_data.original_name
        payment.receipt_content_type = receipt_data.content_type
        payment.receipt_size = receipt_data.size
        payment.save(
            update_fields=[
                "receipt",
                "receipt_original_name",
                "receipt_content_type",
                "receipt_size",
            ],
        )
        if old_name and old_name != new_name and old_storage:
            transaction.on_commit(lambda: old_storage.delete(old_name))
        return payment


def delete_receipt(*, payment_id: int, actor) -> Payment:
    """Delete a pending payment receipt without changing its payment state."""
    with transaction.atomic():
        payment, _debt = _lock_receipt_payment(payment_id, actor)
        old_name = payment.receipt.name if payment.receipt else ""
        old_storage = payment.receipt.storage if payment.receipt else None
        payment.receipt = ""
        payment.receipt_original_name = ""
        payment.receipt_content_type = ""
        payment.receipt_size = None
        payment.save(
            update_fields=[
                "receipt",
                "receipt_original_name",
                "receipt_content_type",
                "receipt_size",
            ],
        )
        if old_name and old_storage:
            transaction.on_commit(lambda: old_storage.delete(old_name))
        return payment
