from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.http import content_disposition_header
from django.utils.translation import gettext as _
from django.views import View

from pixu.charges.models import Debt

from .forms import PaymentForm
from .forms import ReceiptForm
from .models import Payment
from .services import confirm_payment
from .services import delete_receipt
from .services import payment_balance
from .services import record_payment
from .services import reject_payment
from .services import replace_receipt


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _accessible_debt(debt_id: int, actor):
    return get_object_or_404(
        Debt.objects.select_related(
            "participation__charge",
            "creditor",
            "creditor__pix_profile",
            "debtor",
        ),
        pk=debt_id,
        participation__charge__state="ACTIVE",
        debtor=actor,
    )


def _payment_context(  # noqa: PLR0913 - keeps HTMX/form state explicit
    debt,
    form=None,
    status_message="",
    *,
    status_is_error=False,
    receipt_form=None,
    receipt_payment_id=None,
):
    debt.payment_balance = payment_balance(debt)
    payments = list(debt.payments.select_related("confirmed_by", "rejected_by"))
    for payment in payments:
        payment.receipt_form = (
            receipt_form
            if receipt_form is not None and payment.pk == receipt_payment_id
            else ReceiptForm()
        )
    debt.payment_items = payments
    return {
        "debt": debt,
        "payment_balance": debt.payment_balance,
        "payments": payments,
        "form": form or PaymentForm(debt),
        "status_message": status_message,
        "status_is_error": status_is_error,
    }


class PaymentCreateView(LoginRequiredMixin, View):
    def get(self, request, debt_id: int):
        debt = _accessible_debt(debt_id, request.user)
        return render(
            request,
            "settlements/payment_form.html",
            _payment_context(debt),
        )

    def post(self, request, debt_id: int):
        debt = _accessible_debt(debt_id, request.user)
        form = PaymentForm(debt, data=request.POST, files=request.FILES)
        if form.is_valid():
            try:
                record_payment(
                    debt_id=debt.pk,
                    actor=request.user,
                    amount_cents=form.amount_cents,
                    reference=form.cleaned_data["reference"],
                    receipt=form.cleaned_data.get("receipt"),
                )
            except (PermissionDenied, ValidationError) as error:
                if isinstance(error, PermissionDenied):
                    raise
                for message in error.messages:
                    form.add_error(None, message)
            else:
                if _is_htmx(request):
                    debt = _accessible_debt(debt.pk, request.user)
                    return render(
                        request,
                        "settlements/partials/payment_state.html",
                        _payment_context(
                            debt,
                            status_message=(
                                _("Pagamento registrado e aguardando confirmação.")
                            ),
                        ),
                    )
                messages.success(
                    request,
                    _("Pagamento registrado e aguardando confirmação do recebedor."),
                )
                return redirect("charges:detail", pk=debt.participation.charge_id)

        context = _payment_context(
            debt,
            form=form,
            status_message=_("Revise os dados do pagamento."),
            status_is_error=True,
        )
        if _is_htmx(request):
            return render(
                request,
                "settlements/partials/payment_form.html",
                context,
                status=400,
            )
        return render(request, "settlements/payment_form.html", context, status=400)


class PaymentDecisionView(LoginRequiredMixin, View):
    action = ""

    def post(self, request, payment_id: int):
        payment = get_object_or_404(
            Payment.objects.select_related("debt__participation__charge"),
            pk=payment_id,
        )
        try:
            if self.action == "confirm":
                confirm_payment(payment_id=payment.pk, actor=request.user)
                message = "Pagamento confirmado."
            else:
                reject_payment(payment_id=payment.pk, actor=request.user)
                message = "Pagamento rejeitado; o valor voltou a ficar disponível."
        except PermissionDenied:
            raise
        except ValidationError as error:
            message = error.messages[0]
            if _is_htmx(request):
                payment.refresh_from_db()
                return render(
                    request,
                    "settlements/partials/payment_state.html",
                    _payment_context(
                        payment.debt,
                        status_message=message,
                        status_is_error=True,
                    ),
                    status=400,
                )
            messages.error(request, message)
        else:
            if _is_htmx(request):
                payment.refresh_from_db()
                return render(
                    request,
                    "settlements/partials/payment_state.html",
                    _payment_context(payment.debt, status_message=message),
                )
            messages.success(request, message)
        return redirect("charges:detail", pk=payment.debt.participation.charge_id)


class ConfirmPaymentView(PaymentDecisionView):
    action = "confirm"


class RejectPaymentView(PaymentDecisionView):
    action = "reject"


class PaymentReceiptView(LoginRequiredMixin, View):
    def get(self, request, payment_id: int):
        payment = get_object_or_404(
            Payment.objects.select_related(
                "debt__participation__charge",
            ),
            pk=payment_id,
        )
        if request.user.pk not in {
            payment.debt.debtor_id,
            payment.debt.creditor_id,
            payment.debt.participation.charge.creator_id,
        }:
            raise PermissionDenied
        if not payment.receipt:
            raise Http404
        try:
            file_handle = payment.receipt.open("rb")
        except (FileNotFoundError, OSError) as error:
            raise Http404 from error
        response = FileResponse(
            file_handle,
            content_type=payment.receipt_content_type or "application/octet-stream",
        )
        filename = payment.receipt_original_name or "comprovante"
        response["Content-Disposition"] = content_disposition_header(
            as_attachment=False,
            filename=filename,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class GuestPaymentReceiptView(View):
    """Deliver a guest's private receipt only for its own participation."""

    def get(self, request, payment_id: int, participation_id: int, code: str):
        payment = get_object_or_404(
            Payment.objects.select_related("debt__participation__charge"),
            pk=payment_id,
            debt__participation_id=participation_id,
        )
        from pixu.charges.services import get_guest_participation
        from pixu.charges.guest_views import _session_allows

        get_guest_participation(participation_id=participation_id, personal_code=code)
        if not _session_allows(request, participation_id):
            raise PermissionDenied
        if not payment.receipt:
            raise PermissionDenied
        try:
            file_handle = payment.receipt.open("rb")
        except (FileNotFoundError, OSError) as error:
            raise Http404 from error
        response = FileResponse(
            file_handle,
            content_type=payment.receipt_content_type or "application/octet-stream",
        )
        response["Content-Disposition"] = content_disposition_header(
            as_attachment=False,
            filename=payment.receipt_original_name or "comprovante",
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class PaymentReceiptUpdateView(LoginRequiredMixin, View):
    def post(self, request, payment_id: int):
        payment = get_object_or_404(
            Payment.objects.select_related("debt__participation__charge"),
            pk=payment_id,
        )
        form = ReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                replace_receipt(
                    payment_id=payment.pk,
                    actor=request.user,
                    receipt=form.cleaned_data["receipt"],
                )
            except (PermissionDenied, ValidationError) as error:
                if isinstance(error, PermissionDenied):
                    raise
                form.add_error("receipt", error.messages)
            else:
                if _is_htmx(request):
                    payment.refresh_from_db()
                    return render(
                        request,
                        "settlements/partials/payment_state.html",
                        _payment_context(
                            payment.debt,
                            status_message=_("Comprovante atualizado."),
                        ),
                    )
                messages.success(request, _("Comprovante atualizado."))
                return redirect(
                    "charges:detail",
                    pk=payment.debt.participation.charge_id,
                )
        if _is_htmx(request):
            payment.refresh_from_db()
            return render(
                request,
                "settlements/partials/payment_state.html",
                _payment_context(
                    payment.debt,
                    status_message=_("Revise o arquivo enviado."),
                    status_is_error=True,
                    receipt_form=form,
                    receipt_payment_id=payment.pk,
                ),
                status=400,
            )
        messages.error(request, _("Revise o arquivo enviado."))
        return redirect("charges:detail", pk=payment.debt.participation.charge_id)


class PaymentReceiptDeleteView(LoginRequiredMixin, View):
    def post(self, request, payment_id: int):
        payment = get_object_or_404(
            Payment.objects.select_related("debt__participation__charge"),
            pk=payment_id,
        )
        try:
            delete_receipt(payment_id=payment.pk, actor=request.user)
        except PermissionDenied:
            raise
        except ValidationError as error:
            message = error.messages[0]
            if _is_htmx(request):
                payment.refresh_from_db()
                return render(
                    request,
                    "settlements/partials/payment_state.html",
                    _payment_context(
                        payment.debt,
                        status_message=message,
                        status_is_error=True,
                    ),
                    status=400,
                )
            messages.error(request, message)
        else:
            if _is_htmx(request):
                payment.refresh_from_db()
                return render(
                    request,
                    "settlements/partials/payment_state.html",
                    _payment_context(
                        payment.debt,
                        status_message=_("Comprovante removido."),
                    ),
                )
            messages.success(request, _("Comprovante removido."))
        return redirect("charges:detail", pk=payment.debt.participation.charge_id)
