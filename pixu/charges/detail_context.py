from __future__ import annotations

from collections import defaultdict
from copy import copy
from dataclasses import dataclass

from django.db.models import Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from pixu.settlements.forms import CompensationForm
from pixu.settlements.forms import ReceiptForm
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment
from pixu.settlements.services import PaymentBalance
from pixu.settlements.services import suggest_compensations

from .forms import ChargeCancellationForm
from .forms import ChargeItemForm
from .forms import ChargeSharesForm
from .forms import ReplaceParticipantForm
from .models import Charge
from .models import Debt
from .models import Participation


@dataclass
class ChargeDetailState:
    share_form: ChargeSharesForm | None = None
    item_form: ChargeItemForm | None = None
    replacement_form: ReplaceParticipantForm | None = None
    replacement_participation_id: int | None = None
    compensation_form: CompensationForm | None = None
    compensation_debt_id: int | None = None
    compensation_reciprocal_debt_id: int | None = None
    compensation_preview_amount_cents: int | None = None
    cancellation_form: ChargeCancellationForm | None = None
    status_message: str = ""
    status_is_error: bool = False


@dataclass
class ReceiverParticipationLine:
    """A receiver-safe, presentation-only summary of one participation."""

    participation: Participation
    debt: Debt | None
    is_own_share: bool
    identity_group: str
    order_key: tuple
    open_age_label: str = ""

    @property
    def pending_payments(self):
        if self.debt is None:
            return []
        return [
            payment
            for payment in self.debt.payment_items
            if payment.state == Payment.State.PENDING
        ]

    @property
    def has_financial_history(self) -> bool:
        if self.debt is None:
            return False
        return bool(self.debt.payment_items or self.debt.compensation_items)

    @property
    def extra_items(self):
        """Individual extras already included in this participant's share."""
        return self.participation.items.all()

    @property
    def extra_charges_cents(self) -> int:
        return sum(item.amount_cents for item in self.extra_items)


def _attach_creator_receipts(charge, actor, participations):
    if charge.creator_id != actor.pk:
        return
    receipts_by_participation = defaultdict(list)
    receipts = (
        Payment.objects.filter(debt__participation__charge=charge)
        .exclude(receipt="")
        .select_related("debt__participation")
        .order_by("created_at", "pk")
    )
    for payment in receipts:
        receipts_by_participation[payment.debt.participation_id].append(payment)
    for participation in participations:
        participation.receipt_payments = receipts_by_participation[participation.pk]


def _load_debts_with_financial_state(charge, actor):
    debts = list(
        Debt.objects.filter(participation__charge=charge)
        .filter(Q(debtor=actor) | Q(creditor=actor))
        .select_related(
            "debtor",
            "debtor__pix_profile",
            "creditor",
            "creditor__pix_profile",
            "participation",
        )
        .order_by("pk"),
    )
    if not debts:
        return debts

    debt_ids = [debt.pk for debt in debts]
    debt_id_set = set(debt_ids)
    payment_items_by_debt = defaultdict(list)
    for payment in (
        Payment.objects.filter(debt_id__in=debt_ids)
        .select_related("confirmed_by", "rejected_by")
        .order_by("-created_at", "-pk")
    ):
        payment.receipt_form = ReceiptForm()
        payment_items_by_debt[payment.debt_id].append(payment)

    payment_totals = {
        row["debt_id"]: row
        for row in Payment.objects.filter(debt_id__in=debt_ids)
        .values("debt_id")
        .annotate(
            confirmed=Coalesce(
                Sum(
                    "amount_cents",
                    filter=Q(state=Payment.State.CONFIRMED),
                ),
                0,
            ),
            pending=Coalesce(
                Sum(
                    "amount_cents",
                    filter=Q(state=Payment.State.PENDING),
                ),
                0,
            ),
        )
    }
    compensation_items_by_debt = defaultdict(list)
    compensated_by_debt = defaultdict(int)
    compensations = (
        Compensation.objects.filter(
            Q(debt_id__in=debt_ids) | Q(reciprocal_debt_id__in=debt_ids),
        )
        .select_related(
            "debt__participation__charge",
            "reciprocal_debt__participation__charge",
            "initiated_by",
        )
        .order_by("-created_at", "-pk")
    )
    for compensation in compensations:
        for debt_id, other_debt in (
            (compensation.debt_id, compensation.reciprocal_debt),
            (compensation.reciprocal_debt_id, compensation.debt),
        ):
            if debt_id not in debt_id_set:
                continue
            compensation_item = copy(compensation)
            compensation_item.other_debt = other_debt
            compensation_items_by_debt[debt_id].append(compensation_item)
            compensated_by_debt[debt_id] += compensation.amount_cents

    for debt in debts:
        totals = payment_totals.get(debt.pk, {})
        confirmed = int(totals.get("confirmed", 0) or 0)
        pending = int(totals.get("pending", 0) or 0)
        compensated = int(compensated_by_debt[debt.pk])
        original = int(debt.original_cents)
        open_cents = max(original - confirmed - compensated, 0)
        debt.payment_balance = PaymentBalance(
            original_cents=original,
            confirmed_cents=confirmed,
            compensated_cents=compensated,
            pending_cents=pending,
            open_cents=open_cents,
            available_cents=max(open_cents - pending, 0),
        )
        debt.payment_items = payment_items_by_debt[debt.pk]
        debt.compensation_items = compensation_items_by_debt[debt.pk]
        debt.compensation_options = []

    return debts


def _build_compensation_options(debts, actor, state):
    for debt in debts:
        if debt.debtor_id != actor.pk:
            continue
        for option in suggest_compensations(debt_id=debt.pk, actor=actor):
            form = (
                state.compensation_form
                if (
                    state.compensation_debt_id == debt.pk
                    and state.compensation_reciprocal_debt_id
                    == option.reciprocal_debt.pk
                )
                else CompensationForm(
                    option,
                    prefix=f"compensation-{debt.pk}-{option.reciprocal_debt.pk}",
                )
            )
            form.fields["amount"].widget.attrs.update(
                {
                    "hx-get": reverse(
                        "charges:compensation_preview",
                        args=[debt.pk, option.reciprocal_debt.pk],
                    ),
                    "hx-trigger": "input changed delay:300ms, change",
                    "hx-include": "closest form",
                    "hx-target": (
                        f"#compensation-preview-{debt.pk}-"
                        f"{option.reciprocal_debt.pk}"
                    ),
                    "hx-swap": "innerHTML",
                },
            )
            is_current_form = (
                state.compensation_debt_id == debt.pk
                and state.compensation_reciprocal_debt_id == option.reciprocal_debt.pk
            )
            preview_amount_cents = (
                state.compensation_preview_amount_cents
                if is_current_form
                and state.compensation_preview_amount_cents is not None
                else option.max_amount_cents
            )
            debt.compensation_options.append(
                {
                    "option": option,
                    "form": form,
                    "preview_amount_cents": preview_amount_cents,
                    "preview_remaining_cents": (
                        option.current_available_cents - preview_amount_cents
                    ),
                },
            )


def _age_label(debt):
    days_open = max((timezone.now() - debt.created_at).days, 0)
    if days_open == 0:
        return "Em aberto hoje"
    if days_open == 1:
        return "Em aberto há 1 dia"
    return f"Em aberto há {days_open} dias"


def _receiver_participant_groups(participations, debts, actor):
    debts_by_participation = {debt.participation_id: debt for debt in debts}
    groups = {"pixu": [], "guest": []}
    for participation in participations:
        debt = debts_by_participation.get(participation.pk)
        is_own_share = participation.user_id == actor.pk
        identity_group = "pixu" if participation.user_id else "guest"
        open_age_label = ""
        if is_own_share:
            attention = 0
        elif participation.state == Participation.State.PENDING or debt is None:
            attention = 5
        elif any(
            payment.state == Payment.State.PENDING for payment in debt.payment_items
        ):
            attention = 1
        elif debt.payment_balance.open_cents:
            has_financial_history = bool(
                debt.payment_items or debt.compensation_items,
            )
            attention = 3 if has_financial_history else 2
            if not has_financial_history:
                open_age_label = _age_label(debt)
        else:
            attention = 4
        created_at = debt.created_at if debt is not None else participation.invited_at
        groups[identity_group].append(
            ReceiverParticipationLine(
                participation=participation,
                debt=debt,
                is_own_share=is_own_share,
                identity_group=identity_group,
                order_key=(attention, created_at, participation.pk),
                open_age_label=open_age_label,
            ),
        )
    return [
        {
            "key": "pixu",
            "title": "Contas Pixu",
            "lines": sorted(groups["pixu"], key=lambda line: line.order_key),
        },
        {
            "key": "guest",
            "title": "Convites Anônimos",
            "lines": sorted(groups["guest"], key=lambda line: line.order_key),
        },
    ]


def charge_detail_context(
    charge: Charge,
    actor,
    state: ChargeDetailState | None = None,
):
    """Build the shared detail context without issuing one financial query per row."""

    state = state or ChargeDetailState()
    participations = list(
        charge.participations.select_related("user").prefetch_related("items").order_by(
            "user_id",
            "pk",
        ),
    )
    _attach_creator_receipts(charge, actor, participations)
    can_edit = (
        charge.creator_id == actor.pk
        and charge.locked_at is None
        and charge.state != Charge.State.CANCELLED
    )
    can_cancel = charge.creator_id == actor.pk and charge.state in {
        Charge.State.ACTIVE,
        Charge.State.AWAITING_ACCEPTANCE,
    }
    replacement_rows = []
    if can_edit and charge.state == Charge.State.AWAITING_ACCEPTANCE:
        for participation in participations:
            if participation.state != Participation.State.DECLINED:
                continue
            form = (
                state.replacement_form
                if participation.pk == state.replacement_participation_id
                else ReplaceParticipantForm(charge)
            )
            replacement_rows.append({"participation": participation, "form": form})

    my_participation = next(
        (
            participation
            for participation in participations
            if participation.user_id == actor.pk
        ),
        None,
    )
    debts = _load_debts_with_financial_state(charge, actor)
    _build_compensation_options(debts, actor, state)
    is_receiver = charge.creditor_id == actor.pk
    return {
        "charge": charge,
        "participations": participations,
        "guest_entry_count": sum(
            1
            for participation in participations
            if participation.guest_access_digest
            and participation.state
            in (Participation.State.PENDING, Participation.State.ACCEPTED)
        ),
        "my_participation": my_participation,
        "can_edit": can_edit,
        "can_cancel": can_cancel,
        "cancellation_form": (
            state.cancellation_form
            if state.cancellation_form is not None
            else ChargeCancellationForm()
            if can_cancel
            else None
        ),
        "share_form": state.share_form
        or (ChargeSharesForm(charge) if can_edit else None),
        "item_form": state.item_form or (ChargeItemForm(charge) if can_edit else None),
        "replacement_rows": replacement_rows,
        "status_message": state.status_message,
        "status_is_error": state.status_is_error,
        "debts": debts,
        "is_receiver": is_receiver,
        "receiver_participant_groups": (
            _receiver_participant_groups(participations, debts, actor)
            if is_receiver
            else []
        ),
    }


def add_guest_session_context(context, request, charge):
    """Keep creator-only guest credentials across a full detail HTMX swap."""

    credentials = request.session.get(f"pixu_guest_credentials:{charge.pk}")
    context["guest_credentials"] = credentials
    context["guest_share_url"] = (
        request.build_absolute_uri(
            reverse("charges:guest_entry", args=[charge.pk, credentials["token"]]),
        )
        if credentials
        else ""
    )
    return context
