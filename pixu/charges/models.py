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
GUEST_NAME_MAX_LENGTH = 120
GUEST_TOKEN_DIGEST_MAX_LENGTH = 64
DEFAULT_GUEST_ENTRY_LIMIT = 10
DEFAULT_GUEST_ACCESS_TTL_DAYS = 7
MAX_GUEST_TOTAL_PARTICIPANTS = 100


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
    guest_invites_enabled = models.BooleanField(
        _("entradas anônimas habilitadas"),
        default=False,
    )
    guest_total_participants = models.PositiveSmallIntegerField(
        _("total explícito de participantes"),
        null=True,
        blank=True,
    )
    guest_entry_limit = models.PositiveSmallIntegerField(
        _("limite de entradas convidadas"),
        default=DEFAULT_GUEST_ENTRY_LIMIT,
    )
    guest_access_ttl_days = models.PositiveSmallIntegerField(
        _("validade do acesso convidado em dias"),
        default=DEFAULT_GUEST_ACCESS_TTL_DAYS,
    )
    guest_entries_open = models.BooleanField(
        _("entradas convidadas abertas"),
        default=False,
    )
    guest_entries_closed_at = models.DateTimeField(
        _("entradas fechadas em"),
        null=True,
        blank=True,
    )
    guest_entry_token_digest = models.CharField(
        _("digest do link convidado"),
        max_length=GUEST_TOKEN_DIGEST_MAX_LENGTH,
        blank=True,
    )
    guest_entry_code_digest = models.CharField(
        _("digest do código convidado"),
        max_length=GUEST_TOKEN_DIGEST_MAX_LENGTH,
        blank=True,
    )
    guest_entry_token_created_at = models.DateTimeField(
        _("link convidado criado em"),
        null=True,
        blank=True,
    )
    guest_entry_token_revoked_at = models.DateTimeField(
        _("link convidado revogado em"),
        null=True,
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
            models.CheckConstraint(
                condition=Q(guest_entry_limit__gte=1, guest_entry_limit__lte=100),
                name="guest_entry_limit_valid",
            ),
            models.CheckConstraint(
                condition=Q(guest_total_participants__isnull=True)
                | Q(guest_total_participants__gte=1, guest_total_participants__lte=100),
                name="guest_total_participants_valid",
            ),
            models.CheckConstraint(
                condition=Q(guest_access_ttl_days__gte=1, guest_access_ttl_days__lte=30),
                name="guest_access_ttl_valid",
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
        null=True,
        blank=True,
    )
    guest_name = models.CharField(
        _("nome autodeclarado do convidado"),
        max_length=GUEST_NAME_MAX_LENGTH,
        blank=True,
        null=True,
    )
    guest_name_normalized = models.CharField(
        _("nome convidado normalizado"),
        max_length=GUEST_NAME_MAX_LENGTH,
        blank=True,
        null=True,
    )
    guest_access_digest = models.CharField(
        _("digest do código pessoal"),
        max_length=GUEST_TOKEN_DIGEST_MAX_LENGTH,
        blank=True,
    )
    guest_access_created_at = models.DateTimeField(
        _("código pessoal criado em"),
        null=True,
        blank=True,
    )
    guest_access_expires_at = models.DateTimeField(
        _("código pessoal expira em"),
        null=True,
        blank=True,
    )
    guest_claimed_at = models.DateTimeField(
        _("entrada convidada em"),
        null=True,
        blank=True,
    )
    share_cents = models.PositiveBigIntegerField(_("cota em centavos"))
    base_share_cents = models.PositiveBigIntegerField(
        _("parcela da base comum em centavos"),
        default=0,
    )
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
            models.CheckConstraint(
                condition=(
                    Q(user__isnull=False, guest_name__isnull=True)
                    | Q(user__isnull=True, guest_name__isnull=False)
                ),
                name="participation_single_identity",
            ),
        ]

    def __str__(self) -> str:
        identity = self.user or self.guest_name or "Convidado"
        return f"{identity} — {self.charge}"


class ChargeItem(models.Model):
    """An optional individual extra assigned to one participation."""

    DESCRIPTION_MAX_LENGTH = 160

    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("cobrança"),
    )
    participation = models.ForeignKey(
        Participation,
        on_delete=models.SET_NULL,
        related_name="items",
        verbose_name=_("responsável"),
        null=True,
        blank=True,
    )
    description = models.CharField(
        _("descrição"),
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    amount_cents = models.PositiveBigIntegerField(_("valor em centavos"))
    created_at = models.DateTimeField(_("criado em"), default=timezone.now, editable=False)

    class Meta:
        ordering = ["pk"]
        verbose_name = _("item da cobrança")
        verbose_name_plural = _("itens da cobrança")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0),
                name="charge_item_amount_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.description} — {self.amount_cents}¢"


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
        null=True,
        blank=True,
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
                condition=Q(debtor__isnull=True) | ~Q(debtor=F("creditor")),
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
