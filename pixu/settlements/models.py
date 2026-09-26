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
                condition=Q(state__in=("PENDING", "CONFIRMED", "REJECTED")),
                name="payment_state_valid",
            ),
            models.CheckConstraint(
                condition=~Q(payer=F("creditor")),
                name="payment_parties_must_differ",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.payer} → {self.creditor}: {self.amount_cents}¢ ({self.state})"
