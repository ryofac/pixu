from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView

from .forms import AcceptParticipationForm
from .forms import ChargeAllocationForm
from .forms import ChargeCreateForm
from .forms import ChargeSharesForm
from .forms import ReplaceParticipantForm
from .models import Charge
from .models import Participation
from .services import accept_participation
from .services import create_charge
from .services import decline_participation
from .services import edit_participation_shares
from .services import replace_declined_participant

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http import HttpResponse


@dataclass
class ChargeDetailState:
    share_form: ChargeSharesForm | None = None
    replacement_form: ReplaceParticipantForm | None = None
    replacement_participation_id: int | None = None
    status_message: str = ""
    status_is_error: bool = False


def _visible_charges(user):
    return (
        Charge.objects.filter(
            Q(creator=user) | Q(creditor=user) | Q(participations__user=user),
        )
        .select_related("creator", "creditor")
        .prefetch_related("participations__user")
        .distinct()
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
    can_edit = charge.creator_id == actor.pk and charge.locked_at is None
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
    return {
        "charge": charge,
        "participations": participations,
        "my_participation": my_participation,
        "can_edit": can_edit,
        "share_form": state.share_form
        or (ChargeSharesForm(charge) if can_edit else None),
        "replacement_rows": replacement_rows,
        "status_message": state.status_message,
        "status_is_error": state.status_is_error,
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


class ChargeListView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["charges"] = _visible_charges(self.request.user)
        else:
            context["charges"] = Charge.objects.none()
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
        if preview or (allocation_form.is_bound and not allocation_form.is_valid()):
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
                shares_by_user=allocation_form.shares_by_user,
            )
        except ValidationError as error:
            form.add_error(None, error.messages)
            return self.form_invalid(form)
        messages.success(
            self.request,
            "Cobrança criada. Convites aguardam resposta."
            if charge.state == Charge.State.AWAITING_ACCEPTANCE
            else "Cobrança criada e ativa.",
        )
        return redirect("charges:detail", pk=charge.pk)


def _allocation_context(form, data=None):
    allocation_form = None
    if (
        form.cleaned_data.get("total") is not None
        and form.cleaned_data.get("invitees") is not None
        and form.participants
    ):
        has_manual_shares = data is not None and any(
            key.startswith("share_") for key in data
        )
        allocation_form = ChargeAllocationForm(
            people=form.participants,
            total_cents=form.total_cents,
            data=data if has_manual_shares else None,
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


class ChargeDetailView(LoginRequiredMixin, DetailView):
    template_name = "charges/charge_detail.html"
    context_object_name = "charge"

    def get_queryset(self):
        return _visible_charges(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_charge_detail_context(self.object, self.request.user))
        return context


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
                status_message = "Sua participação foi aceita."
            else:
                decline_participation(
                    participation_id=participation.pk,
                    actor=request.user,
                )
                status_message = "Convite recusado. Nenhuma dívida foi criada."
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
        status_message = "Revise as cotas antes de salvar." if invalid else ""
        status_is_error = invalid

        if not invalid:
            try:
                edit_participation_shares(
                    charge_id=charge.pk,
                    shares_by_participation=form.shares_by_participation,
                    actor=request.user,
                    creditor_id=form.cleaned_data["creditor"].pk,
                )
                status_message = "Cotas e recebedor atualizados."
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
            "Escolha uma conta válida para substituir o convite." if invalid else ""
        )
        status_is_error = invalid

        if not invalid:
            try:
                replace_declined_participant(
                    participation_id=declined.pk,
                    replacement_user_id=form.cleaned_data["replacement"].pk,
                    actor=request.user,
                )
                status_message = "Novo convite enviado."
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
