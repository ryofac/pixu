from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from weasyprint import HTML

from .forms import ExtractFilterForm
from .queries import PaidEvent
from .queries import debts_with_compensation_options
from .queries import grouped_open_debts
from .queries import paid_events

if TYPE_CHECKING:
    from pixu.charges.models import Debt


EXTRACTS = {
    "payable": {"title": _("A pagar")},
    "receivable": {"title": _("A receber")},
    "paid": {"title": _("Já pago")},
}


def _extract_result(*, kind: str, actor, form: ExtractFilterForm):
    if not form.is_valid():
        form.mark_invalid_fields_for_accessibility()
        return []
    query = form.cleaned_data.get("q", "")
    if kind == "paid":
        return paid_events(
            actor=actor,
            search=query,
            date_from=form.cleaned_data.get("date_from"),
            date_to=form.cleaned_data.get("date_to"),
        )
    return grouped_open_debts(actor=actor, direction=kind, search=query)


def _query_string(form: ExtractFilterForm) -> str:
    if not form.is_valid():
        return ""
    values = {}
    for key, value in form.cleaned_data.items():
        if value:
            values[key] = value.isoformat() if isinstance(value, date) else value
    return urlencode(values)


def _paid_total(events: list[PaidEvent]) -> int:
    return sum(
        event.amount_cents
        for event in events
        if not (event.event_type == "payment" and event.state == "REVOKED")
    )


class FinancialExtractView(LoginRequiredMixin, TemplateView):
    template_name = "extracts/extract.html"
    extract_kind = "payable"

    def get_filter_form(self):
        return ExtractFilterForm(
            self.request.GET,
            include_dates=self.extract_kind == "paid",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_filter_form()
        results = _extract_result(
            kind=self.extract_kind,
            actor=self.request.user,
            form=form,
        )
        paginator = Paginator(results, 25 if self.extract_kind == "paid" else 20)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        if self.extract_kind != "paid":
            page_debts = [
                debt
                for group in page_obj.object_list
                for debt in group.debts
            ]
            compensation_debt_ids = (
                debts_with_compensation_options(
                    self.request.user,
                    [debt.pk for debt in page_debts],
                )
                if self.extract_kind == "payable"
                else set()
            )
            for debt in page_debts:
                debt.compensation_recommended = debt.pk in compensation_debt_ids
            total_cents = sum(group.total_cents for group in results)
        else:
            total_cents = _paid_total(results)
        context.update(
            {
                "extract_kind": self.extract_kind,
                "extract_title": EXTRACTS[self.extract_kind]["title"],
                "filter_form": form,
                "page_obj": page_obj,
                "results": page_obj.object_list,
                "total_cents": total_cents,
                "query_string": _query_string(form),
            },
        )
        return context


class PayableExtractView(FinancialExtractView):
    extract_kind = "payable"


class ReceivableExtractView(FinancialExtractView):
    extract_kind = "receivable"


class PaidExtractView(FinancialExtractView):
    extract_kind = "paid"


def _safe_csv_text(value) -> str:
    text = "" if value is None else str(value)
    first_non_space = text.lstrip(" \t\r\n")
    if first_non_space.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _event_row(event: PaidEvent) -> dict:
    return {
        "type": "Pagamento" if event.event_type == "payment" else "Compensação",
        "event_id": event.event_id,
        "source_record_id": event.source_pk,
        "debt_id": event.debt_id,
        "charge_id": event.charge_id,
        "charge_title": event.charge_title,
        "counterparty": event.counterparty,
        "effective_at": timezone.localtime(event.effective_at),
        "recorded_at": timezone.localtime(event.recorded_at),
        "state": event.state_label,
        "original_cents": "",
        "open_cents": "",
        "amount_cents": event.amount_cents,
        "confirmation_source": event.confirmation_source_label,
        "reference": event.reference,
        "receipt_present": "Sim" if event.receipt_present else "Não",
        "compensation_request_id": event.compensation_request_id,
        "paired_debt_id": event.paired_debt_id or "",
        "paired_charge_title": event.paired_charge_title,
    }


def _debt_row(group, debt: Debt) -> dict:
    return {
        "type": "Dívida em aberto",
        "event_id": f"debt:{debt.pk}",
        "source_record_id": debt.pk,
        "debt_id": debt.pk,
        "charge_id": debt.participation.charge_id,
        "charge_title": debt.participation.charge.title,
        "counterparty": group.name,
        "effective_at": timezone.localtime(debt.created_at),
        "recorded_at": timezone.localtime(debt.created_at),
        "state": "Em aberto",
        "original_cents": int(debt.original_cents),
        "open_cents": int(debt.open_cents),
        "amount_cents": int(debt.open_cents),
        "confirmation_source": "",
        "reference": "",
        "receipt_present": "Não",
        "compensation_request_id": "",
        "paired_debt_id": "",
        "paired_charge_title": "",
    }


def _export_rows(kind: str, results) -> list[dict]:
    if kind == "paid":
        return [_event_row(event) for event in results]
    return [
        _debt_row(group, debt)
        for group in results
        for debt in group.debts
    ]


CSV_COLUMNS = [
    ("Tipo", "type"),
    ("ID do evento", "event_id"),
    ("ID do registro", "source_record_id"),
    ("ID da dívida", "debt_id"),
    ("ID da cobrança", "charge_id"),
    ("Cobrança", "charge_title"),
    ("Pessoa", "counterparty"),
    ("Data efetiva", "effective_at"),
    ("Data de registro", "recorded_at"),
    ("Situação atual", "state"),
    ("Valor original (centavos)", "original_cents"),
    ("Saldo aberto (centavos)", "open_cents"),
    ("Valor do evento (centavos)", "amount_cents"),
    ("Origem da confirmação", "confirmation_source"),
    ("Referência", "reference"),
    ("Comprovante anexado", "receipt_present"),
    ("ID da compensação", "compensation_request_id"),
    ("ID da dívida relacionada", "paired_debt_id"),
    ("Cobrança relacionada", "paired_charge_title"),
]


def _csv_response(*, kind: str, rows: list[dict]) -> HttpResponse:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow([label for label, _field in CSV_COLUMNS])
    for row in rows:
        writer.writerow(
            [
                _safe_csv_text(row[field])
                if isinstance(row[field], (str, type(None)))
                else row[field]
                for _label, field in CSV_COLUMNS
            ],
        )
    response = HttpResponse(
        "\ufeff" + buffer.getvalue(),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="pixu-{kind}.csv"'
    return response


def _deny_url_fetcher(_url):
    raise ValueError


class ExtractExportView(LoginRequiredMixin, View):
    format = "csv"

    def get(self, request, kind: str):
        if kind not in EXTRACTS:
            raise Http404
        form = ExtractFilterForm(
            request.GET,
            include_dates=kind == "paid",
        )
        if not form.is_valid():
            form.mark_invalid_fields_for_accessibility()
            return render(
                request,
                "extracts/extract.html",
                {
                    "extract_kind": kind,
                    "extract_title": EXTRACTS[kind]["title"],
                    "filter_form": form,
                    "page_obj": None,
                    "results": [],
                    "total_cents": 0,
                    "query_string": "",
                },
                status=400,
            )
        results = _extract_result(kind=kind, actor=request.user, form=form)
        rows = _export_rows(kind, results)
        if self.format == "csv":
            return _csv_response(kind=kind, rows=rows)
        total_cents = (
            _paid_total(results)
            if kind == "paid"
            else sum(int(row["open_cents"]) for row in rows)
        )
        html = render_to_string(
            "extracts/extract_pdf.html",
            {
                "extract_title": EXTRACTS[kind]["title"],
                "rows": rows,
                "total_cents": total_cents,
                "generated_at": timezone.localtime(),
                "filters": form.cleaned_data,
                "is_paid": kind == "paid",
            },
            request=request,
        )
        document = HTML(string=html, url_fetcher=_deny_url_fetcher).write_pdf()
        response = HttpResponse(document, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="pixu-{kind}.pdf"'
        return response


class CsvExtractExportView(ExtractExportView):
    format = "csv"


class PdfExtractExportView(ExtractExportView):
    format = "pdf"
