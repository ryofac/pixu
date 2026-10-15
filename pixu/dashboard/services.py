from __future__ import annotations

from pixu.accounts.models import PixProfile
from pixu.charges.models import Charge
from pixu.charges.models import Participation
from pixu.extracts.queries import dashboard_financial_summary


def dashboard_context(user) -> dict:
    """Build a read-only dashboard summary from the shared extract queries."""
    financial = dashboard_financial_summary(user)

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
        **financial,
        "pending_invites": pending_invites,
        "created_charges": created_charges,
        "participated_charges": participated_charges,
        "pix_key_missing": not pix_key or not pix_key.strip(),
    }
