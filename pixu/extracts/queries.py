from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models import BigIntegerField
from django.db.models import Count
from django.db.models import Exists
from django.db.models import Min
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.models import Participation
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment
from pixu.settlements.services import with_payment_balances

if TYPE_CHECKING:
    from datetime import date
    from datetime import datetime


@dataclass(frozen=True)
class CounterpartyPreview:
    key: str
    name: str
    total_cents: int
    oldest_at: datetime
    debt_count: int


@dataclass
class DebtGroup:
    key: str
    name: str
    total_cents: int
    oldest_at: datetime
    debts: list[Debt]


@dataclass(frozen=True)
class PaidEvent:
    event_type: str
    event_id: str
    source_pk: int
    debt_id: int
    charge_id: int
    charge_title: str
    counterparty: str
    amount_cents: int
    effective_at: datetime
    recorded_at: datetime
    state: str
    state_label: str
    confirmation_source: str
    confirmation_source_label: str
    reference: str
    receipt_present: bool
    compensation_request_id: str = ""
    paired_debt_id: int | None = None
    paired_charge_id: int | None = None
    paired_charge_title: str = ""


def open_debts(*, actor, direction: str, search: str = ""):
    """Return only active, accepted, positive-balance debts in one direction."""
    if direction == "payable":
        scope = Q(debtor_id=actor.pk)
    elif direction == "receivable":
        scope = Q(creditor_id=actor.pk)
    else:
        raise ValueError

    queryset = (
        with_payment_balances(
            Debt.objects.filter(
                scope,
                participation__state=Participation.State.ACCEPTED,
                participation__charge__state=Charge.State.ACTIVE,
            ),
        )
        .filter(open_cents__gt=0)
        .select_related(
            "debtor",
            "creditor",
            "participation",
            "participation__user",
            "participation__charge",
        )
    )
    if search:
        if direction == "payable":
            search_scope = (
                Q(creditor__name__icontains=search)
                | Q(creditor__username__icontains=search)
            )
        else:
            search_scope = (
                Q(debtor__name__icontains=search)
                | Q(debtor__username__icontains=search)
                | Q(participation__guest_name__icontains=search)
            )
        queryset = queryset.filter(
            search_scope | Q(participation__charge__title__icontains=search),
        )
    return queryset.order_by("created_at", "pk")


def debts_with_compensation_options(actor, debt_ids: list[int]) -> set[int]:
    if not debt_ids:
        return set()
    reciprocal_debts = with_payment_balances(
        Debt.objects.filter(
            debtor_id=OuterRef("creditor_id"),
            creditor_id=actor.pk,
            participation__state=Participation.State.ACCEPTED,
            participation__charge__state=Charge.State.ACTIVE,
        ).exclude(pk=OuterRef("pk")),
    ).filter(available_cents__gt=0)
    return set(
        open_debts(actor=actor, direction="payable")
        .filter(pk__in=debt_ids, available_cents__gt=0)
        .annotate(has_reciprocal=Exists(reciprocal_debts))
        .filter(has_reciprocal=True)
        .values_list("pk", flat=True),
    )


def _display_name(user, fallback: str = "") -> str:
    if user is None:
        return fallback.strip() or "Convidado"
    return user.name.strip() or user.username


def _summary_rows(queryset, *, direction: str) -> list[CounterpartyPreview]:
    previews: list[CounterpartyPreview] = []
    if direction == "payable":
        rows = (
            queryset.values("creditor_id", "creditor__name", "creditor__username")
            .annotate(
                total=Sum("open_cents"),
                oldest=Min("created_at"),
                debt_count=Count("pk"),
            )
            .order_by("oldest", "creditor_id")
        )
        for row in rows:
            name = row["creditor__name"].strip() or row["creditor__username"]
            previews.append(
                CounterpartyPreview(
                    key=f"user:{row['creditor_id']}",
                    name=name,
                    total_cents=int(row["total"] or 0),
                    oldest_at=row["oldest"],
                    debt_count=row["debt_count"],
                ),
            )
    else:
        account_rows = (
            queryset.filter(debtor__isnull=False)
            .values("debtor_id", "debtor__name", "debtor__username")
            .annotate(
                total=Sum("open_cents"),
                oldest=Min("created_at"),
                debt_count=Count("pk"),
            )
            .order_by("oldest", "debtor_id")
        )
        guest_rows = (
            queryset.filter(debtor__isnull=True)
            .values("participation_id", "participation__guest_name")
            .annotate(
                total=Sum("open_cents"),
                oldest=Min("created_at"),
                debt_count=Count("pk"),
            )
            .order_by("oldest", "participation_id")
        )
        previews.extend(
            CounterpartyPreview(
                key=f"user:{row['debtor_id']}",
                name=row["debtor__name"].strip() or row["debtor__username"],
                total_cents=int(row["total"] or 0),
                oldest_at=row["oldest"],
                debt_count=row["debt_count"],
            )
            for row in account_rows
        )
        previews.extend(
            CounterpartyPreview(
                key=f"participation:{row['participation_id']}",
                name=(row["participation__guest_name"] or "").strip()
                or "Convidado",
                total_cents=int(row["total"] or 0),
                oldest_at=row["oldest"],
                debt_count=row["debt_count"],
            )
            for row in guest_rows
        )
        previews.sort(key=lambda preview: (preview.oldest_at, preview.key))
    return previews[:5]


def dashboard_financial_summary(actor) -> dict:
    payable = open_debts(actor=actor, direction="payable")
    receivable = open_debts(actor=actor, direction="receivable")
    payable_total = int(payable.aggregate(total=Sum("open_cents"))["total"] or 0)
    receivable_total = int(receivable.aggregate(total=Sum("open_cents"))["total"] or 0)
    payable_preview = _summary_rows(payable, direction="payable")
    receivable_preview = _summary_rows(receivable, direction="receivable")

    active_accepted = Q(
        debt__participation__state=Participation.State.ACCEPTED,
        debt__participation__charge__state=Charge.State.ACTIVE,
    )
    confirmed_total = Payment.objects.filter(
        active_accepted,
        debt__debtor_id=actor.pk,
        state=Payment.State.CONFIRMED,
    ).aggregate(total=Coalesce(Sum("amount_cents"), zero_bigint()))["total"]
    compensation_total = Compensation.objects.filter(
        Q(
            debt__debtor_id=actor.pk,
            debt__participation__state=Participation.State.ACCEPTED,
            debt__participation__charge__state=Charge.State.ACTIVE,
        )
        | Q(
            reciprocal_debt__debtor_id=actor.pk,
            reciprocal_debt__participation__state=Participation.State.ACCEPTED,
            reciprocal_debt__participation__charge__state=Charge.State.ACTIVE,
        ),
        debt__participation__state=Participation.State.ACCEPTED,
        debt__participation__charge__state=Charge.State.ACTIVE,
        reciprocal_debt__participation__state=Participation.State.ACCEPTED,
        reciprocal_debt__participation__charge__state=Charge.State.ACTIVE,
    ).aggregate(total=Coalesce(Sum("amount_cents"), zero_bigint()))["total"]
    return {
        "payable_cents": payable_total,
        "receivable_cents": receivable_total,
        "paid_cents": int(confirmed_total or 0) + int(compensation_total or 0),
        "payable_preview": payable_preview,
        "receivable_preview": receivable_preview,
    }


def zero_bigint():
    return Value(0, output_field=BigIntegerField())


def grouped_open_debts(*, actor, direction: str, search: str = "") -> list[DebtGroup]:
    grouped: dict[str, DebtGroup] = {}
    for debt in open_debts(actor=actor, direction=direction, search=search):
        if direction == "payable":
            key = f"user:{debt.creditor_id}"
            name = _display_name(debt.creditor)
        elif debt.debtor_id:
            key = f"user:{debt.debtor_id}"
            name = _display_name(debt.debtor)
        else:
            key = f"participation:{debt.participation_id}"
            name = _display_name(None, debt.participation.guest_name or "")
        debt.counterparty_name = name
        group = grouped.get(key)
        if group is None:
            group = DebtGroup(
                key=key,
                name=name,
                total_cents=0,
                oldest_at=debt.created_at,
                debts=[],
            )
            grouped[key] = group
        group.total_cents += int(debt.open_cents)
        group.debts.append(debt)
    return sorted(grouped.values(), key=lambda group: (group.oldest_at, group.key))


def _event_matches_dates(
    event: PaidEvent,
    start: date | None,
    end: date | None,
) -> bool:
    effective_date = timezone.localtime(event.effective_at).date()
    return (start is None or effective_date >= start) and (
        end is None or effective_date <= end
    )


def paid_events(
    *,
    actor,
    search: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[PaidEvent]:
    payments = Payment.objects.filter(
        debt__debtor_id=actor.pk,
        debt__participation__state=Participation.State.ACCEPTED,
        confirmed_at__isnull=False,
    ).filter(
        Q(
            state=Payment.State.CONFIRMED,
            debt__participation__charge__state=Charge.State.ACTIVE,
        )
        | Q(state=Payment.State.REVOKED),
    )
    if search:
        payments = payments.filter(
            Q(creditor__name__icontains=search)
            | Q(creditor__username__icontains=search)
            | Q(debt__participation__charge__title__icontains=search),
        )
    payment_records = payments.select_related(
        "creditor",
        "debt__participation__charge",
    )

    compensations = Compensation.objects.filter(
        Q(debt__debtor_id=actor.pk) | Q(reciprocal_debt__debtor_id=actor.pk),
        debt__participation__state=Participation.State.ACCEPTED,
        debt__participation__charge__state=Charge.State.ACTIVE,
        reciprocal_debt__participation__state=Participation.State.ACCEPTED,
        reciprocal_debt__participation__charge__state=Charge.State.ACTIVE,
    )
    if search:
        compensations = compensations.filter(
            Q(
                debt__debtor_id=actor.pk,
                debt__creditor__name__icontains=search,
            )
            | Q(
                debt__debtor_id=actor.pk,
                debt__creditor__username__icontains=search,
            )
            | Q(
                reciprocal_debt__debtor_id=actor.pk,
                reciprocal_debt__creditor__name__icontains=search,
            )
            | Q(
                reciprocal_debt__debtor_id=actor.pk,
                reciprocal_debt__creditor__username__icontains=search,
            )
            | Q(debt__participation__charge__title__icontains=search)
            | Q(reciprocal_debt__participation__charge__title__icontains=search),
        )
    compensation_records = compensations.select_related(
        "debt__debtor",
        "debt__creditor",
        "debt__participation__charge",
        "reciprocal_debt__debtor",
        "reciprocal_debt__creditor",
        "reciprocal_debt__participation__charge",
    )

    events: list[PaidEvent] = []
    for payment in payment_records:
        event = PaidEvent(
            event_type="payment",
            event_id=f"payment:{payment.pk}",
            source_pk=payment.pk,
            debt_id=payment.debt_id,
            charge_id=payment.debt.participation.charge_id,
            charge_title=payment.debt.participation.charge.title,
            counterparty=_display_name(payment.creditor),
            amount_cents=int(payment.amount_cents),
            effective_at=payment.confirmed_at,
            recorded_at=payment.created_at,
            state=payment.state,
            state_label=payment.get_state_display(),
            confirmation_source=payment.confirmation_source,
            confirmation_source_label=payment.get_confirmation_source_display(),
            reference=payment.reference,
            receipt_present=bool(payment.receipt),
        )
        if _event_matches_dates(event, date_from, date_to):
            events.append(event)

    for compensation in compensation_records:
        if compensation.debt.debtor_id == actor.pk:
            own_debt = compensation.debt
            paired_debt = compensation.reciprocal_debt
        else:
            own_debt = compensation.reciprocal_debt
            paired_debt = compensation.debt
        event = PaidEvent(
            event_type="compensation",
            event_id=f"compensation:{compensation.request_id}",
            source_pk=compensation.pk,
            debt_id=own_debt.pk,
            charge_id=own_debt.participation.charge_id,
            charge_title=own_debt.participation.charge.title,
            counterparty=_display_name(own_debt.creditor),
            amount_cents=int(compensation.amount_cents),
            effective_at=compensation.created_at,
            recorded_at=compensation.created_at,
            state="APPLIED",
            state_label="Compensada",
            confirmation_source="",
            confirmation_source_label="",
            reference="",
            receipt_present=False,
            compensation_request_id=str(compensation.request_id),
            paired_debt_id=paired_debt.pk,
            paired_charge_id=paired_debt.participation.charge_id,
            paired_charge_title=paired_debt.participation.charge.title,
        )
        if _event_matches_dates(event, date_from, date_to):
            events.append(event)
    return sorted(
        events,
        key=lambda event: (event.effective_at, event.event_type, event.source_pk),
        reverse=True,
    )
