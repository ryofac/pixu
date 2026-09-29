from __future__ import annotations

from collections import defaultdict

from django.db.models import BigIntegerField
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Value
from django.db.models.functions import Coalesce

from pixu.accounts.models import PixProfile
from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.models import Participation
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment


def dashboard_context(user) -> dict:
    """Build a read-only dashboard summary from active debt events."""
    debts = list(
        Debt.objects.filter(
            Q(debtor=user) | Q(creditor=user),
            participation__state=Participation.State.ACCEPTED,
            participation__charge__state=Charge.State.ACTIVE,
        )
        .select_related("participation__charge")
        .order_by("pk"),
    )
    debt_ids = [debt.pk for debt in debts]

    payment_rows = (
        Payment.objects.filter(debt_id__in=debt_ids)
        .values("debt_id")
        .annotate(
            confirmed_cents=Coalesce(
                Sum("amount_cents", filter=Q(state=Payment.State.CONFIRMED)),
                Value(0, output_field=BigIntegerField()),
            ),
            pending_cents=Coalesce(
                Sum("amount_cents", filter=Q(state=Payment.State.PENDING)),
                Value(0, output_field=BigIntegerField()),
            ),
        )
    )
    payment_totals = {
        row["debt_id"]: (row["confirmed_cents"], row["pending_cents"])
        for row in payment_rows
    }

    compensated_cents_by_debt = defaultdict(int)
    for row in (
        Compensation.objects.filter(debt_id__in=debt_ids)
        .values("debt_id")
        .annotate(total=Sum("amount_cents"))
    ):
        compensated_cents_by_debt[row["debt_id"]] += row["total"] or 0
    for row in (
        Compensation.objects.filter(reciprocal_debt_id__in=debt_ids)
        .values("reciprocal_debt_id")
        .annotate(total=Sum("amount_cents"))
    ):
        compensated_cents_by_debt[row["reciprocal_debt_id"]] += row["total"] or 0

    receivable_cents = 0
    payable_cents = 0
    available_to_pay_by_person = defaultdict(int)
    available_to_receive_by_person = defaultdict(int)
    for debt in debts:
        confirmed_cents, pending_cents = payment_totals.get(debt.pk, (0, 0))
        open_cents = max(
            debt.original_cents
            - confirmed_cents
            - compensated_cents_by_debt[debt.pk],
            0,
        )
        available_cents = max(open_cents - pending_cents, 0)
        if debt.creditor_id == user.pk:
            receivable_cents += open_cents
            available_to_receive_by_person[debt.debtor_id] += available_cents
        else:
            payable_cents += open_cents
            available_to_pay_by_person[debt.creditor_id] += available_cents

    counterparties = set(available_to_pay_by_person) | set(
        available_to_receive_by_person,
    )
    compensation_potential_cents = sum(
        min(
            available_to_pay_by_person[person_id],
            available_to_receive_by_person[person_id],
        )
        for person_id in counterparties
    )

    pending_invites = (
        Participation.objects.filter(user=user, state=Participation.State.PENDING)
        .select_related("charge", "charge__creator", "charge__creditor")
        .order_by("charge__created_at", "pk")[:5]
    )
    created_charges = (
        Charge.objects.filter(creator=user)
        .select_related("creator", "creditor")
        .prefetch_related("participations__user")
        .order_by("-created_at", "-pk")[:5]
    )
    participated_charges = (
        Charge.objects.filter(participations__user=user)
        .exclude(creator=user)
        .select_related("creator", "creditor")
        .prefetch_related("participations__user")
        .order_by("-created_at", "-pk")
        .distinct()[:5]
    )
    pix_key = (
        PixProfile.objects.filter(user=user)
        .values_list("pix_key", flat=True)
        .first()
    )

    return {
        "receivable_cents": receivable_cents,
        "payable_cents": payable_cents,
        "compensation_potential_cents": compensation_potential_cents,
        "pending_invites": pending_invites,
        "created_charges": created_charges,
        "participated_charges": participated_charges,
        "pix_key_missing": not pix_key or not pix_key.strip(),
    }
