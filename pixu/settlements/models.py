from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pixu.charges.models import Debt

PAYMENT_REFERENCE_MAX_LENGTH = 500


def payment_receipt_upload_to(instance: Payment, filename: str) -> str:
    """Keep receipts under a non-public, per-payment path."""
    return f"private_uploads/payments/{uuid.uuid4().hex}/{filename}"


class Payment(models.Model):
    class State(models.TextChoices):
        PENDING = "PENDING", _("Pendente")
        CONFIRMED = "CONFIRMED", _("Confirmado")
        REJECTED = "REJECTED", _("Rejeitado")
        REVOKED = "REVOKED", _("Revogado")

    class ConfirmationSource(models.TextChoices):
        MANUAL = "MANUAL", _("Manual")
        AUTOMATIC = "AUTOMATIC", _("Automática")

    debt = models.ForeignKey(
        Debt,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("dívida"),
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments_made",
        verbose_name=_("pagador"),
        null=True,
        blank=True,
    )
    creditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments_received",
        verbose_name=_("recebedor"),
    )
    amount_cents = models.PositiveBigIntegerField(_("valor em centavos"))
    reference = models.CharField(
        _("referência"),
        max_length=PAYMENT_REFERENCE_MAX_LENGTH,
        blank=True,
    )
    receipt = models.FileField(
        _("comprovante privado"),
        upload_to=payment_receipt_upload_to,
        blank=True,
    )
    receipt_original_name = models.CharField(
        _("nome original do comprovante"),
        max_length=255,
        blank=True,
    )
    receipt_content_type = models.CharField(
        _("tipo do comprovante"),
        max_length=100,
        blank=True,
    )
    receipt_size = models.PositiveBigIntegerField(
        _("tamanho do comprovante"),
        null=True,
        blank=True,
    )
    state = models.CharField(
        _("estado"),
        choices=State,
        default=State.PENDING,
        max_length=12,
    )
    confirmation_source = models.CharField(
        _("origem da confirmação"),
        choices=ConfirmationSource,
        default=ConfirmationSource.MANUAL,
        max_length=12,
    )
    created_at = models.DateTimeField(
        _("registrado em"),
        default=timezone.now,
        editable=False,
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments_confirmed",
        verbose_name=_("confirmado por"),
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(_("confirmado em"), null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments_rejected",
        verbose_name=_("rejeitado por"),
        null=True,
        blank=True,
    )
    rejected_at = models.DateTimeField(_("rejeitado em"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("pagamento")
        verbose_name_plural = _("pagamentos")
        indexes = [
            models.Index(fields=["debt", "state"]),
            models.Index(fields=["creditor", "state"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0),
                name="payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    state__in=("PENDING", "CONFIRMED", "REJECTED", "REVOKED"),
                ),
                name="payment_state_valid",
            ),
            models.CheckConstraint(
                condition=Q(payer__isnull=True) | ~Q(payer=F("creditor")),
                name="payment_parties_must_differ",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.payer or 'Convidado'} → {self.creditor}: {self.amount_cents}¢ ({self.state})"


class Compensation(models.Model):
    debt = models.ForeignKey(
        Debt,
        on_delete=models.PROTECT,
        related_name="compensations_as_debt",
        verbose_name=_("dívida reduzida"),
    )
    reciprocal_debt = models.ForeignKey(
        Debt,
        on_delete=models.PROTECT,
        related_name="compensations_as_reciprocal_debt",
        verbose_name=_("dívida recíproca reduzida"),
    )
    amount_cents = models.PositiveBigIntegerField(_("valor compensado em centavos"))
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="compensations_initiated",
        verbose_name=_("iniciada por"),
    )
    request_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_("identificador da solicitação"),
    )
    created_at = models.DateTimeField(
        _("aplicada em"),
        default=timezone.now,
        editable=False,
    )

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("compensação")
        verbose_name_plural = _("compensações")
        indexes = [
            models.Index(fields=["debt", "created_at"]),
            models.Index(fields=["reciprocal_debt", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0),
                name="compensation_amount_positive",
            ),
            models.CheckConstraint(
                condition=~Q(debt=F("reciprocal_debt")),
                name="compensation_debts_distinct",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Compensação de {self.amount_cents}¢ entre dívidas "
            f"{self.debt_id} e {self.reciprocal_debt_id}"
        )


class PendingReceiptDeletion(models.Model):
    """Durable outbox entry for retryable private receipt cleanup."""

    storage_alias = models.CharField(_("storage"), max_length=100, default="default")
    file_name = models.CharField(_("chave do arquivo"), max_length=1024)
    queued_at = models.DateTimeField(_("adicionado à fila"), default=timezone.now)

    class Meta:
        ordering = ["queued_at", "pk"]
        verbose_name = _("remoção pendente de comprovante")
        verbose_name_plural = _("remoções pendentes de comprovantes")
        constraints = [
            models.UniqueConstraint(
                fields=["storage_alias", "file_name"],
                name="unique_pending_receipt_deletion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.storage_alias}: {self.file_name}"
