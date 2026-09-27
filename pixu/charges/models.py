from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

CHARGE_TITLE_MAX_LENGTH = 120
CHARGE_DESCRIPTION_MAX_LENGTH = 1000
CHARGE_CANCELLATION_REASON_MAX_LENGTH = 500


class Charge(models.Model):
    class State(models.TextChoices):
        AWAITING_ACCEPTANCE = "AWAITING_ACCEPTANCE", _("Aguardando aceite")
        ACTIVE = "ACTIVE", _("Ativa")
        CANCELLED = "CANCELLED", _("Cancelada")

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_charges",
        verbose_name=_("criador"),
    )
    creditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receivable_charges",
        verbose_name=_("recebedor"),
    )
    title = models.CharField(_("título"), max_length=CHARGE_TITLE_MAX_LENGTH)
    description = models.TextField(
        _("descrição"),
        blank=True,
        max_length=CHARGE_DESCRIPTION_MAX_LENGTH,
    )
    total_cents = models.PositiveBigIntegerField(_("valor total em centavos"))
    state = models.CharField(
        _("estado"),
        choices=State,
        default=State.AWAITING_ACCEPTANCE,
        max_length=24,
    )
    created_at = models.DateTimeField(
        _("criada em"),
        default=timezone.now,
        editable=False,
    )
    locked_at = models.DateTimeField(_("bloqueada em"), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cancelled_charges",
        verbose_name=_("cancelada por"),
        null=True,
        blank=True,
    )
    cancelled_at = models.DateTimeField(_("cancelada em"), null=True, blank=True)
    cancellation_reason = models.CharField(
        _("motivo do cancelamento"),
        max_length=CHARGE_CANCELLATION_REASON_MAX_LENGTH,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("cobrança")
        verbose_name_plural = _("cobranças")
        constraints = [
            models.CheckConstraint(
                condition=Q(total_cents__gt=0),
                name="charge_total_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    state__in=("AWAITING_ACCEPTANCE", "ACTIVE", "CANCELLED"),
                ),
                name="charge_state_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class Participation(models.Model):
    class State(models.TextChoices):
        PENDING = "PENDING", _("Pendente")
        ACCEPTED = "ACCEPTED", _("Aceita")
        DECLINED = "DECLINED", _("Recusada")
        CANCELLED = "CANCELLED", _("Cancelada")

    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="participations",
        verbose_name=_("cobrança"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="charge_participations",
        verbose_name=_("participante"),
    )
    share_cents = models.PositiveBigIntegerField(_("cota em centavos"))
    state = models.CharField(
        _("estado do convite"),
        choices=State,
        default=State.PENDING,
        max_length=12,
    )
    invited_at = models.DateTimeField(
        _("convidada em"),
        default=timezone.now,
        editable=False,
    )
    accepted_at = models.DateTimeField(_("aceita em"), null=True, blank=True)
    declined_at = models.DateTimeField(_("recusada em"), null=True, blank=True)

    class Meta:
        ordering = ["user_id", "pk"]
        verbose_name = _("participação")
        verbose_name_plural = _("participações")
        constraints = [
            models.UniqueConstraint(
                fields=["charge", "user"],
                condition=~Q(state__in=("DECLINED", "CANCELLED")),
                name="one_current_participation_per_user",
            ),
            models.CheckConstraint(
                condition=Q(share_cents__gte=0),
                name="participation_share_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(
                    state__in=("PENDING", "ACCEPTED", "DECLINED", "CANCELLED"),
                ),
                name="participation_state_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.charge}"


class Debt(models.Model):
    participation = models.OneToOneField(
        Participation,
        on_delete=models.PROTECT,
        related_name="debt",
        verbose_name=_("participação aceita"),
    )
    debtor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="debts_to_pay",
        verbose_name=_("devedor"),
    )
    creditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="debts_to_receive",
        verbose_name=_("recebedor"),
    )
    original_cents = models.PositiveBigIntegerField(_("valor original em centavos"))
    created_at = models.DateTimeField(
        _("criada em"),
        default=timezone.now,
        editable=False,
    )

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("dívida")
        verbose_name_plural = _("dívidas")
        constraints = [
            models.CheckConstraint(
                condition=Q(original_cents__gte=0),
                name="debt_original_nonnegative",
            ),
            models.CheckConstraint(
                condition=~Q(debtor=F("creditor")),
                name="debt_parties_must_differ",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.debtor} → {self.creditor}: {self.original_cents}¢"


class ChargeDeletionAudit(models.Model):
    """Minimal audit record that survives absolute charge deletion."""

    charge_id_snapshot = models.PositiveBigIntegerField(
        _("identificador da cobrança excluída"),
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="charge_deletions",
        verbose_name=_("excluída por"),
    )
    deleted_at = models.DateTimeField(_("excluída em"), default=timezone.now)
    reason = models.CharField(
        _("motivo"),
        max_length=CHARGE_CANCELLATION_REASON_MAX_LENGTH,
        blank=True,
    )

    class Meta:
        ordering = ["-deleted_at", "-pk"]
        verbose_name = _("auditoria de exclusão de cobrança")
        verbose_name_plural = _("auditorias de exclusão de cobranças")

    def __str__(self) -> str:
        return f"Cobrança {self.charge_id_snapshot} — {self.deleted_at:%Y-%m-%d %H:%M}"
