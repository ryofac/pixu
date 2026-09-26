from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.charges.models import Charge
from pixu.charges.models import Debt

from .models import PAYMENT_REFERENCE_MAX_LENGTH
from .models import Payment
from .validators import validate_receipt


@dataclass(frozen=True)
class PaymentBalance:
    original_cents: int
    confirmed_cents: int
    pending_cents: int
    open_cents: int
    available_cents: int


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
    confirmed = int(totals["confirmed"] or 0)
    pending = int(totals["pending"] or 0)
    original = int(debt_value.original_cents)
    open_cents = max(original - confirmed, 0)
    return PaymentBalance(
        original_cents=original,
        confirmed_cents=confirmed,
        pending_cents=pending,
        open_cents=open_cents,
        available_cents=max(open_cents - pending, 0),
    )


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
    actor,
    amount_cents: int,
    reference: str = "",
    receipt=None,
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
        if debt.debtor_id != actor.pk:
            raise PermissionDenied
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
            payer_id=debt.debtor_id,
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
