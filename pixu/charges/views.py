from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView

from .forms import ChargeCreateForm
from .models import Charge
from .models import Participation
from .services import accept_participation
from .services import create_charge
from .services import decline_participation


class ChargeListView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["charges"] = (
                Charge.objects.filter(
                    Q(creator=self.request.user)
                    | Q(participations__user=self.request.user),
                )
                .select_related("creator")
                .prefetch_related("participations__user")
                .distinct()
            )
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
            .select_related("charge", "charge__creator")
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

    def form_valid(self, form):
        try:
            charge = create_charge(
                creator=self.request.user,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                total_cents=form.total_cents,
                invitee_ids=form.invitee_ids,
            )
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, "Cobrança criada. Convites aguardam resposta.")
        return redirect("charges:detail", pk=charge.pk)


class ChargeDetailView(LoginRequiredMixin, DetailView):
    template_name = "charges/charge_detail.html"
    context_object_name = "charge"

    def get_queryset(self):
        return (
            Charge.objects.filter(
                Q(creator=self.request.user)
                | Q(participations__user=self.request.user),
            )
            .select_related("creator")
            .prefetch_related("participations__user")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_participation"] = self.object.participations.filter(
            user=self.request.user,
        ).first()
        return context


class ParticipationResponseView(LoginRequiredMixin, View):
    action = ""

    def post(self, request: HttpRequest, pk: int, participation_id: int) -> HttpResponse:
        participation = get_object_or_404(
            Participation.objects.select_related("charge"),
            pk=participation_id,
            charge_id=pk,
            user=request.user,
        )
        try:
            if self.action == "accept":
                accept_participation(participation_id=participation.pk, actor=request.user)
                messages.success(request, "Sua participação foi aceita.")
            else:
                decline_participation(participation_id=participation.pk, actor=request.user)
                messages.success(request, "Convite recusado. Nenhuma dívida foi criada.")
        except PermissionDenied:
            raise
        except ValidationError as error:
            messages.error(request, error.messages[0])
        return redirect(reverse("charges:detail", kwargs={"pk": pk}))


class AcceptParticipationView(ParticipationResponseView):
    action = "accept"


class DeclineParticipationView(ParticipationResponseView):
    action = "decline"


def pending_charge_invites(request: HttpRequest) -> dict[str, int]:
    if not request.user.is_authenticated:
        return {"pending_charge_invites_count": 0}
    return {
        "pending_charge_invites_count": Participation.objects.filter(
            user=request.user,
            state=Participation.State.PENDING,
        ).count(),
    }
