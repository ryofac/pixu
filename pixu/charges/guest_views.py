from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from pixu.accounts.models import PixProfile
from pixu.settlements.forms import PaymentForm
from pixu.settlements.services import payment_balance, record_payment

from .forms import GuestEntryForm
from .models import Charge, Debt, Participation
from .services import confirm_guest_participation
from .services import enter_guest_charge
from .services import get_guest_participation
from .services import leave_guest_participation
from .services import validate_guest_entry_link
from .services import close_guest_entries
from .services import reopen_guest_entries
from .services import rotate_guest_invite
from .services import revoke_guest_invite


SESSION_PARTICIPATION_KEY = "pixu_guest_participation_id"


def _session_allows(request, participation_id: int) -> bool:
    stored = request.session.get(SESSION_PARTICIPATION_KEY)
    if stored is None:
        request.session[SESSION_PARTICIPATION_KEY] = participation_id
        return True
    return int(stored) == participation_id


def _guest_context(participation, *, form=None, status_message="", status_is_error=False):
    charge = participation.charge
    debt = getattr(participation, "debt", None)
    if debt is not None:
        debt.payment_balance = payment_balance(debt)
        if form is None:
            form = PaymentForm(debt)
    pix_key = (
        PixProfile.objects.filter(user_id=charge.creditor_id)
        .values_list("pix_key", flat=True)
        .first()
        or ""
    )
    return {
        "charge": charge,
        "participation": participation,
        "display_name": (
            participation.guest_name
            or (participation.user.name if participation.user else None)
            or (participation.user.username if participation.user else None)
            or _("Convidado")
        ),
        "debt": debt,
        "pix_key": pix_key,
        "payment_balance": getattr(debt, "payment_balance", None),
        "payment_form": form,
        "status_message": status_message,
        "status_is_error": status_is_error,
    }


class GuestEntryView(View):
    template_name = "charges/guest_entry.html"

    def _charge(self, pk):
        return get_object_or_404(Charge.objects.select_related("creator", "creditor"), pk=pk)

    def get(self, request, pk: int, token: str):
        charge = validate_guest_entry_link(charge_id=pk, shared_secret=token)
        form = GuestEntryForm()
        return render(request, self.template_name, {"charge": charge, "form": form, "shared_token": token})

    def post(self, request, pk: int, token: str):
        charge = validate_guest_entry_link(charge_id=pk, shared_secret=token)
        form = GuestEntryForm(request.POST)
        if form.is_valid():
            try:
                access = enter_guest_charge(
                    charge_id=charge.pk,
                    shared_secret=token,
                    name=form.cleaned_data["name"],
                    account_user=request.user if request.user.is_authenticated else None,
                )
            except PermissionDenied:
                raise
            except ValidationError as error:
                form.add_error(None, error.messages)
            else:
                request.session[SESSION_PARTICIPATION_KEY] = access.participation.pk
                return render(
                    request,
                    "charges/guest_access_created.html",
                    {
                        "charge": charge,
                        "participation": access.participation,
                        "personal_code": access.code,
                        "personal_url": request.build_absolute_uri(
                            reverse(
                                "charges:guest_personal",
                                args=[charge.pk, access.participation.pk, access.code],
                            ),
                        ),
                    },
                )
        return render(
            request,
            self.template_name,
            {"charge": charge, "form": form, "shared_token": token},
            status=400,
        )


class GuestPersonalView(View):
    template_name = "charges/guest_personal.html"

    def _participation(self, request, pk, participation_id, code):
        participation = get_object_or_404(
            Participation.objects.select_related("charge", "charge__creator", "charge__creditor"),
            pk=participation_id,
            charge_id=pk,
        )
        get_guest_participation(participation_id=participation.pk, personal_code=code)
        if not _session_allows(request, participation.pk):
            raise PermissionDenied
        return participation

    def get(self, request, pk: int, participation_id: int, code: str):
        participation = self._participation(request, pk, participation_id, code)
        return render(
            request,
            self.template_name,
            _guest_context(participation),
        )

    def post(self, request, pk: int, participation_id: int, code: str):
        participation = self._participation(request, pk, participation_id, code)
        action = request.POST.get("action", "confirm")
        try:
            if action == "leave":
                leave_guest_participation(participation_id=participation.pk, personal_code=code)
                request.session.pop(SESSION_PARTICIPATION_KEY, None)
                return redirect("charges:guest_entry_closed", pk=pk)
            confirm_guest_participation(
                participation_id=participation.pk,
                personal_code=code,
                expected_share_cents=int(request.POST.get("expected_share_cents", 0)),
                expected_creditor_id=int(request.POST.get("expected_creditor_id", 0)),
            )
        except (PermissionDenied, ValidationError) as error:
            if isinstance(error, PermissionDenied):
                raise
            participation.refresh_from_db()
            return render(
                request,
                self.template_name,
                _guest_context(
                    participation,
                    status_message=error.messages[0],
                    status_is_error=True,
                ),
                status=400,
            )
        participation.refresh_from_db()
        return render(
            request,
            self.template_name,
            _guest_context(participation, status_message=_("Sua cota foi confirmada.")),
        )


class GuestEntryClosedView(View):
    def get(self, request, pk: int):
        charge = get_object_or_404(Charge, pk=pk)
        return render(request, "charges/guest_entry_closed.html", {"charge": charge})


class GuestPaymentView(View):
    template_name = "charges/guest_personal.html"

    def post(self, request, participation_id: int, code: str):
        participation = get_object_or_404(
            Participation.objects.select_related("charge", "charge__creator", "charge__creditor"),
            pk=participation_id,
        )
        get_guest_participation(participation_id=participation.pk, personal_code=code)
        if not _session_allows(request, participation.pk):
            raise PermissionDenied
        debt = get_object_or_404(
            Debt.objects.select_related("participation__charge"),
            participation=participation,
        )
        form = PaymentForm(debt, data=request.POST, files=request.FILES)
        if form.is_valid():
            try:
                record_payment(
                    debt_id=debt.pk,
                    actor=None,
                    guest_participation_id=participation.pk,
                    guest_code=code,
                    amount_cents=form.amount_cents,
                    reference=form.cleaned_data["reference"],
                    receipt=form.cleaned_data.get("receipt"),
                )
            except (PermissionDenied, ValidationError) as error:
                if isinstance(error, PermissionDenied):
                    raise
                form.add_error(None, error.messages)
            else:
                participation.refresh_from_db()
                return render(
                    request,
                    self.template_name,
                    _guest_context(
                        participation,
                        status_message=_("Pagamento registrado e aguardando confirmação."),
                    ),
                )
        participation.refresh_from_db()
        return render(
            request,
            self.template_name,
            _guest_context(
                participation,
                form=form,
                status_message=_("Revise os dados do pagamento."),
                status_is_error=True,
            ),
            status=400,
        )


class GuestEntriesManageView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        action = request.POST.get("action", "")
        try:
            if action == "close":
                close_guest_entries(charge_id=pk, actor=request.user)
            elif action == "reopen":
                reopen_guest_entries(charge_id=pk, actor=request.user)
            elif action == "rotate":
                credentials = rotate_guest_invite(charge_id=pk, actor=request.user)
                request.session[f"pixu_guest_credentials:{pk}"] = credentials
            elif action == "revoke":
                revoke_guest_invite(charge_id=pk, actor=request.user)
            else:
                raise ValidationError(_("Ação de entrada desconhecida."))
        except PermissionDenied:
            raise
        except ValidationError as error:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse(error.messages[0], status=400)
            raise
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(status=204)
        return redirect("charges:detail", pk=pk)
