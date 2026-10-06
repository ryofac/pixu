from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView

from pixu.accounts.models import PixProfile
from pixu.settlements.forms import CompensationForm
from pixu.settlements.forms import ReceiptForm
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment
from pixu.settlements.services import apply_compensation
from pixu.settlements.services import payment_balance
from pixu.settlements.services import suggest_compensations

from .forms import AcceptParticipationForm
from .forms import ChargeAllocationForm
from .forms import ChargeCancellationForm
from .forms import ChargeCreateForm
from .forms import ChargeItemForm
from .forms import ChargeSharesForm
from .forms import ReplaceParticipantForm
from .models import Charge
from .models import Debt
from .models import Participation
from .services import accept_participation
from .services import add_charge_item
from .services import cancel_charge
from .services import create_charge
from .services import decline_participation
from .services import edit_participation_shares
from .services import replace_declined_participant

if TYPE_CHECKING:
    from django.http import HttpRequest


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


def _visible_charges(user):
    return (
        Charge.objects.filter(
            Q(creator=user) | Q(creditor=user) | Q(participations__user=user),
        )
        .select_related("creator", "creditor")
        .select_related("cancelled_by")
        .prefetch_related("participations__user")
        .distinct()
    )


def _attach_creator_receipts(charge, actor, participations):
    if charge.creator_id != actor.pk:
        return
    receipts_by_participation = {}
    receipts = (
        Payment.objects.filter(debt__participation__charge=charge)
        .exclude(receipt="")
        .select_related("debt__participation")
        .order_by("created_at", "pk")
    )
    for payment in receipts:
        receipts_by_participation.setdefault(payment.debt.participation_id, []).append(
            payment,
        )
    for participation in participations:
        participation.receipt_payments = receipts_by_participation.get(
            participation.pk,
            [],
        )


def _charge_detail_context(
    charge: Charge,
    actor,
    state: ChargeDetailState | None = None,
):
    state = state or ChargeDetailState()
    participations = list(
        charge.participations.select_related("user").order_by("user_id", "pk"),
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
    debts = list(
        Debt.objects.filter(
            participation__charge=charge,
        )
        .filter(Q(debtor=actor) | Q(creditor=actor))
        .select_related(
            "debtor",
            "debtor__pix_profile",
            "creditor",
            "creditor__pix_profile",
            "participation",
        )
        .prefetch_related("payments__confirmed_by", "payments__rejected_by")
        .order_by("pk"),
    )
    for debt in debts:
        debt.payment_balance = payment_balance(debt)
        debt.payment_items = list(debt.payments.all())
        for payment in debt.payment_items:
            payment.receipt_form = ReceiptForm()
        compensation_items = list(
            Compensation.objects.filter(Q(debt=debt) | Q(reciprocal_debt=debt))
            .select_related(
                "debt__participation__charge",
                "reciprocal_debt__participation__charge",
                "initiated_by",
            )
            .order_by("-created_at", "-pk"),
        )
        for compensation in compensation_items:
            compensation.other_debt = (
                compensation.reciprocal_debt
                if compensation.debt_id == debt.pk
                else compensation.debt
            )
        debt.compensation_items = compensation_items
        debt.compensation_options = []
        if debt.debtor_id == actor.pk:
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
                    and state.compensation_reciprocal_debt_id
                    == option.reciprocal_debt.pk
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
    }


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _detail_response(request, charge, context, *, invalid=False):
    if _is_htmx(request):
        return render(request, "charges/partials/charge_state.html", context)
    return render(
        request,
        "charges/charge_detail.html",
        context,
        status=400 if invalid else 200,
    )


class ChargeListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/charge_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["charges"] = _visible_charges(self.request.user)
        return context


class InviteListView(LoginRequiredMixin, TemplateView):
    template_name = "charges/invite_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invites"] = (
            Participation.objects.filter(
                user=self.request.user,
                state=Participation.State.PENDING,
            )
            .select_related("charge", "charge__creator", "charge__creditor")
            .prefetch_related("charge__participations__user")
        )
        return context


class ChargeCreateView(LoginRequiredMixin, FormView):
    template_name = "charges/charge_form.html"
    form_class = ChargeCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        pix_key = PixProfile.objects.filter(user=self.request.user).values_list(
            "pix_key",
            flat=True,
        ).first()
        selected_creditor = form["creditor"].value()
        context["current_user_pix_key_missing"] = not pix_key or not pix_key.strip()
        context["show_creditor_pix_warning"] = (
            context["current_user_pix_key_missing"]
            and str(selected_creditor) == str(self.request.user.pk)
        )
        if form.is_bound and "allocation_form" not in context:
            form.is_valid()
            context.update(_allocation_context(form, data=self.request.POST))
        return context

    def form_valid(self, form):
        preview = self.request.POST.get("intent") == "preview"
        context = _allocation_context(
            form,
            data=None if preview else self.request.POST,
        )
        allocation_form = context["allocation_form"]
        if preview or (
            allocation_form is not None
            and allocation_form.is_bound
            and not allocation_form.is_valid()
        ):
            return self.render_to_response(self.get_context_data(form=form, **context))
        try:
            charge = create_charge(
                creator=self.request.user,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                total_cents=form.total_cents,
                invitee_ids=form.invitee_ids,
                creditor_id=form.cleaned_data["creditor"].pk,
                include_creator=form.cleaned_data["include_creator"],
                shares_by_user=allocation_form.shares_by_user if allocation_form else None,
                guest_invites_enabled=form.cleaned_data.get("guest_invites_enabled", False),
                guest_total_participants=form.cleaned_data.get("guest_total_participants"),
                guest_entry_limit=form.cleaned_data.get("guest_entry_limit") or 10,
                guest_access_ttl_days=form.cleaned_data.get("guest_access_ttl_days") or 7,
            )
        except ValidationError as error:
            form.add_error(None, error.messages)
            return self.form_invalid(form)
        messages.success(
            self.request,
            _("Cobrança criada. Convites aguardam resposta.")
            if charge.state == Charge.State.AWAITING_ACCEPTANCE
            else _("Cobrança criada e ativa."),
        )
        credentials = getattr(charge, "_guest_credentials", None)
        if credentials:
            self.request.session[f"pixu_guest_credentials:{charge.pk}"] = credentials
        return redirect("charges:detail", pk=charge.pk)


def _allocation_context(form, data=None):
    allocation_form = None
    if (
        form.cleaned_data.get("total") is not None
        and form.cleaned_data.get("invitees") is not None
        and form.participants
    ):
        posted_share_fields = (
            {key for key in data if key.startswith("share_")}
            if data is not None
            else set()
        )
        current_share_fields = {
            f"share_{person.pk}" for person in form.participants
        }
        has_current_manual_shares = bool(posted_share_fields) and (
            posted_share_fields == current_share_fields
        )
        fixed_participant_count = (
            form.cleaned_data.get("guest_total_participants")
            if form.cleaned_data.get("guest_invites_enabled")
            else None
        )
        allocation_form = ChargeAllocationForm(
            people=form.participants,
            total_cents=form.total_cents,
            participant_count=fixed_participant_count,
            data=(data if has_current_manual_shares and fixed_participant_count is None else None),
        )
    return {
        "allocation_form": allocation_form,
        "total_cents": form.total_cents if allocation_form else None,
        "preview_errors": [
            *form.errors.get("total", []),
            *form.errors.get("invitees", []),
            *form.errors.get("creditor", []),
        ],
    }


class ChargeCreatePreviewView(LoginRequiredMixin, View):
    """Return a server-calculated share preview without creating a charge."""

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ChargeCreateForm(actor=request.user, data=request.POST)
        form.is_valid()
        return render(
            request,
            "charges/partials/share_preview.html",
            _allocation_context(form),
        )


class GuestOptionsPreviewView(LoginRequiredMixin, View):
    """Return the anonymous-entry options after the checkbox changes."""

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ChargeCreateForm(actor=request.user, data=request.POST)
        form.is_valid()
        return render(
            request,
            "charges/partials/guest_options.html",
            {"form": form},
        )


class ChargeDetailView(LoginRequiredMixin, DetailView):
    template_name = "charges/charge_detail.html"
    context_object_name = "charge"

    def get_queryset(self):
        return _visible_charges(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_charge_detail_context(self.object, self.request.user))
        context["guest_credentials"] = self.request.session.get(
            f"pixu_guest_credentials:{self.object.pk}",
        )
        context["guest_share_url"] = (
            self.request.build_absolute_uri(
                reverse(
                    "charges:guest_entry",
                    args=[self.object.pk, context["guest_credentials"]["token"]],
                ),
            )
            if context["guest_credentials"]
            else ""
        )
        return context


class ChargeItemCreateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        if charge.creator_id != request.user.pk:
            raise PermissionDenied
        form = ChargeItemForm(charge, data=request.POST)
        status_message = ""
        status_is_error = False
        if form.is_valid():
            try:
                add_charge_item(
                    charge_id=charge.pk,
                    actor=request.user,
                    description=form.cleaned_data["description"],
                    amount_cents=form.amount_cents,
                    participation_id=form.cleaned_data["participation"].pk,
                )
            except (PermissionDenied, ValidationError) as error:
                if isinstance(error, PermissionDenied):
                    raise
                form.add_error(None, error.messages)
            else:
                status_message = _("Item adicionado e cotas recalculadas.")
        if not status_message:
            status_message = _("Revise os dados do item.")
            status_is_error = True
        charge.refresh_from_db()
        context = _charge_detail_context(
            charge,
            request.user,
            ChargeDetailState(
                item_form=form,
                status_message=status_message,
                status_is_error=status_is_error,
            ),
        )
        if _is_htmx(request):
            return render(request, "charges/partials/charge_state.html", context, status=400 if status_is_error else 200)
        if status_is_error:
            return render(request, "charges/charge_detail.html", {"charge": charge, **context}, status=400)
        return redirect("charges:detail", pk=charge.pk)


class ChargeCancelView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        if charge.creator_id != request.user.pk:
            raise PermissionDenied

        form = ChargeCancellationForm(data=request.POST)
        invalid = not form.is_valid()
        status_message = ""
        status_is_error = invalid
        if invalid:
            status_message = _("Revise o motivo do cancelamento.")
        else:
            try:
                cancel_charge(
                    charge_id=charge.pk,
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
            except PermissionDenied:
                raise
            except ValidationError as error:
                form.add_error(None, error.messages)
                status_message = error.messages[0]
                invalid = True
                status_is_error = True
            else:
                status_message = _(
                    "Cobrança cancelada. Os pagamentos permanecem no histórico "
                    "como revogados; não há estorno de transferências externas.",
                )

        if not invalid and not _is_htmx(request):
            messages.success(request, status_message)
            return redirect("charges:detail", pk=charge.pk)

        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        context = _charge_detail_context(
            charge,
            request.user,
            ChargeDetailState(
                cancellation_form=form if invalid else None,
                status_message=status_message,
                status_is_error=status_is_error,
            ),
        )
        return _detail_response(request, charge, context, invalid=invalid)


def _compensation_debt(debt_id: int, actor):
    return get_object_or_404(
        Debt.objects.select_related("participation__charge"),
        pk=debt_id,
        debtor=actor,
        participation__charge__state=Charge.State.ACTIVE,
    )


def _eligible_compensation_option(debt: Debt, reciprocal_debt_id: int, actor):
    return next(
        (
            option
            for option in suggest_compensations(debt_id=debt.pk, actor=actor)
            if option.reciprocal_debt.pk == reciprocal_debt_id
        ),
        None,
    )


def _compensation_page_response(
    request,
    debt: Debt,
    state: ChargeDetailState,
):
    context = _charge_detail_context(debt.participation.charge, request.user, state)
    return _detail_response(
        request,
        debt.participation.charge,
        context,
        invalid=state.status_is_error,
    )


class CompensationPreviewView(LoginRequiredMixin, View):
    def get(self, request, debt_id: int, reciprocal_debt_id: int):
        debt = _compensation_debt(debt_id, request.user)
        option = _eligible_compensation_option(debt, reciprocal_debt_id, request.user)
        if option is None:
            return render(
                request,
                "settlements/partials/compensation_preview.html",
                {
                    "preview_status_message": (
                        _("Esta dívida não está mais disponível para compensação.")
                    ),
                },
                status=400,
            )
        form = CompensationForm(
            option,
            data=request.GET,
            prefix=f"compensation-{debt.pk}-{reciprocal_debt_id}",
        )
        if not form.is_valid():
            return render(
                request,
                "settlements/partials/compensation_preview.html",
                {"preview_form": form},
                status=400,
            )
        amount_cents = form.amount_cents
        return render(
            request,
            "settlements/partials/compensation_preview.html",
            {
                "amount_cents": amount_cents,
                "remaining_cents": option.current_available_cents - amount_cents,
            },
        )


class CompensationApplyView(LoginRequiredMixin, View):
    def post(self, request, debt_id: int, reciprocal_debt_id: int):
        debt = _compensation_debt(debt_id, request.user)
        option = _eligible_compensation_option(debt, reciprocal_debt_id, request.user)
        if option is None:
            return _compensation_page_response(
                request,
                debt,
                ChargeDetailState(
                    status_message=_(
                        "A disponibilidade mudou. Confira os valores atualizados "
                        "antes de tentar novamente.",
                    ),
                    status_is_error=True,
                ),
            )

        form = CompensationForm(
            option,
            data=request.POST,
            prefix=f"compensation-{debt.pk}-{reciprocal_debt_id}",
        )
        if not form.is_valid():
            return _compensation_page_response(
                request,
                debt,
                ChargeDetailState(
                    compensation_form=form,
                    compensation_debt_id=debt.pk,
                    compensation_reciprocal_debt_id=reciprocal_debt_id,
                    status_message=_("Revise os dados da compensação."),
                    status_is_error=True,
                ),
            )
        if request.POST.get("intent") == "preview":
            return _compensation_page_response(
                request,
                debt,
                ChargeDetailState(
                    compensation_form=form,
                    compensation_debt_id=debt.pk,
                    compensation_reciprocal_debt_id=reciprocal_debt_id,
                    compensation_preview_amount_cents=form.amount_cents,
                    status_message=_(
                        "Prévia atualizada; nenhuma compensação foi aplicada.",
                    ),
                    status_is_error=False,
                ),
            )
        try:
            apply_compensation(
                debt_id=debt.pk,
                reciprocal_debt_id=option.reciprocal_debt.pk,
                actor=request.user,
                amount_cents=form.amount_cents,
                request_id=form.cleaned_data["request_id"],
            )
        except PermissionDenied:
            raise
        except ValidationError as error:
            for message in error.messages:
                form.add_error(None, message)
            return _compensation_page_response(
                request,
                debt,
                ChargeDetailState(
                    compensation_form=form,
                    compensation_debt_id=debt.pk,
                    compensation_reciprocal_debt_id=reciprocal_debt_id,
                    status_message=_("Revise os dados da compensação."),
                    status_is_error=True,
                ),
            )

        messages.success(
            request,
            _(
                "Compensação aplicada. As duas dívidas foram reduzidas; "
                "nenhum Pix foi realizado.",
            ),
        )
        detail_url = reverse("charges:detail", args=[debt.participation.charge_id])
        if _is_htmx(request):
            response = HttpResponse()
            response["HX-Redirect"] = detail_url
            return response
        return redirect(detail_url)


class ParticipationResponseView(LoginRequiredMixin, View):
    action = ""

    def post(
        self,
        request: HttpRequest,
        pk: int,
        participation_id: int,
    ) -> HttpResponse:
        participation = get_object_or_404(
            Participation.objects.select_related("charge"),
            pk=participation_id,
            charge_id=pk,
            user=request.user,
        )
        status_message = ""
        status_is_error = False
        try:
            if self.action == "accept":
                consent = AcceptParticipationForm(request.POST).validated_terms()
                accept_participation(
                    participation_id=participation.pk,
                    actor=request.user,
                    **consent,
                )
                status_message = _("Sua participação foi aceita.")
            else:
                decline_participation(
                    participation_id=participation.pk,
                    actor=request.user,
                )
                status_message = _("Convite recusado. Nenhuma dívida foi criada.")
        except PermissionDenied:
            raise
        except ValidationError as error:
            status_message = error.messages[0]
            status_is_error = True

        if _is_htmx(request):
            if request.headers.get("HX-Target") == f"invite-{participation.pk}":
                participation = get_object_or_404(
                    Participation.objects.select_related(
                        "charge",
                        "charge__creator",
                        "charge__creditor",
                    ).prefetch_related("charge__participations__user"),
                    pk=participation.pk,
                    user=request.user,
                )
                response = render(
                    request,
                    "charges/partials/invite_card.html",
                    {
                        "participation": participation,
                        "status_message": status_message,
                        "status_is_error": status_is_error,
                    },
                )
                response["HX-Trigger"] = json.dumps(
                    {
                        "pixu:pending-invites-updated": {
                            "count": Participation.objects.filter(
                                user=request.user,
                                state=Participation.State.PENDING,
                            ).count(),
                        },
                    },
                )
                return response
            charge = get_object_or_404(_visible_charges(request.user), pk=pk)
            context = _charge_detail_context(
                charge,
                request.user,
                ChargeDetailState(
                    status_message=status_message,
                    status_is_error=status_is_error,
                ),
            )
            return render(request, "charges/partials/charge_state.html", context)

        if status_message:
            if status_is_error:
                messages.error(request, status_message)
            else:
                messages.success(request, status_message)
        return redirect(reverse("charges:detail", kwargs={"pk": pk}))


class AcceptParticipationView(ParticipationResponseView):
    action = "accept"


class DeclineParticipationView(ParticipationResponseView):
    action = "decline"


class ChargeSharesUpdateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        if charge.creator_id != request.user.pk:
            raise PermissionDenied
        form = ChargeSharesForm(charge, data=request.POST)
        invalid = not form.is_valid()
        status_message = _("Revise as cotas antes de salvar.") if invalid else ""
        status_is_error = invalid

        if not invalid:
            try:
                edit_participation_shares(
                    charge_id=charge.pk,
                    shares_by_participation=form.shares_by_participation,
                    actor=request.user,
                    creditor_id=form.cleaned_data["creditor"].pk,
                )
                status_message = _("Cotas e recebedor atualizados.")
            except PermissionDenied:
                raise
            except ValidationError as error:
                form.add_error(None, error)
                invalid = True
                status_message = error.messages[0]
                status_is_error = True

        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        context = _charge_detail_context(
            charge,
            request.user,
            ChargeDetailState(
                share_form=form if invalid else None,
                status_message=status_message,
                status_is_error=status_is_error,
            ),
        )
        return _detail_response(request, charge, context, invalid=invalid)


class ReplaceParticipantView(LoginRequiredMixin, View):
    def post(
        self,
        request: HttpRequest,
        pk: int,
        participation_id: int,
    ) -> HttpResponse:
        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        if charge.creator_id != request.user.pk:
            raise PermissionDenied
        declined = get_object_or_404(
            charge.participations,
            pk=participation_id,
            state=Participation.State.DECLINED,
        )
        form = ReplaceParticipantForm(charge, data=request.POST)
        invalid = not form.is_valid()
        status_message = (
            _("Escolha uma conta válida para substituir o convite.") if invalid else ""
        )
        status_is_error = invalid

        if not invalid:
            try:
                replace_declined_participant(
                    participation_id=declined.pk,
                    replacement_user_id=form.cleaned_data["replacement"].pk,
                    actor=request.user,
                )
                status_message = _("Novo convite enviado.")
            except PermissionDenied:
                raise
            except ValidationError as error:
                form.add_error(None, error)
                invalid = True
                status_message = error.messages[0]
                status_is_error = True

        charge = get_object_or_404(_visible_charges(request.user), pk=pk)
        if not invalid:
            form = ReplaceParticipantForm(charge)
        context = _charge_detail_context(
            charge,
            request.user,
            ChargeDetailState(
                replacement_form=form,
                replacement_participation_id=declined.pk,
                status_message=status_message,
                status_is_error=status_is_error,
            ),
        )
        return _detail_response(request, charge, context, invalid=invalid)


def pending_charge_invites(request: HttpRequest) -> dict[str, int]:
    if not request.user.is_authenticated:
        return {"pending_charge_invites_count": 0}
    return {
        "pending_charge_invites_count": Participation.objects.filter(
            user=request.user,
            state=Participation.State.PENDING,
        ).count(),
    }
