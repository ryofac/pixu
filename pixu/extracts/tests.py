from __future__ import annotations

from uuid import uuid4

# ruff: noqa: PLR2004
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from pixu.accounts.models import User
from pixu.charges.models import Debt
from pixu.charges.services import accept_participation
from pixu.charges.services import cancel_charge
from pixu.charges.services import create_charge
from pixu.settlements.services import apply_compensation
from pixu.settlements.services import confirm_payment
from pixu.settlements.services import record_payment


class FinancialExtractWorkflowTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(username="ana-extract", name="Ana")
        self.bruno = User.objects.create_user(
            username="bruno-extract",
            name="Bruno",
        )
        self.carla = User.objects.create_user(
            username="carla-extract",
            name="Carla",
        )
        self.diego = User.objects.create_user(
            username="diego-extract",
            name="Diego",
        )

        self.jantar, self.jantar_debt = self.create_debt(
            debtor=self.ana,
            creditor=self.bruno,
            title="Jantar de Ana para Bruno",
            total_cents=10_000,
        )
        self.uber, self.uber_debt = self.create_debt(
            debtor=self.ana,
            creditor=self.bruno,
            title="Uber de Ana para Bruno",
            total_cents=5_000,
        )
        self.cinema, self.cinema_debt = self.create_debt(
            debtor=self.carla,
            creditor=self.ana,
            title="Cinema de Carla para Ana",
            total_cents=8_000,
        )
        self.almoco, self.almoco_debt = self.create_debt(
            debtor=self.bruno,
            creditor=self.ana,
            title="Almoço de Bruno para Ana",
            total_cents=6_000,
        )
        self.viagem, self.viagem_debt = self.create_debt(
            debtor=self.ana,
            creditor=self.carla,
            title="Viagem de Ana para Carla",
            total_cents=3_000,
        )

        payment = record_payment(
            debt_id=self.jantar_debt.pk,
            actor=self.ana,
            amount_cents=2_500,
            reference="Pix confirmado no jantar",
        )
        self.confirmed_payment = confirm_payment(
            payment_id=payment.pk,
            actor=self.bruno,
        )
        self.pending_payment = record_payment(
            debt_id=self.jantar_debt.pk,
            actor=self.ana,
            amount_cents=1_000,
            reference="Pix aguardando confirmação",
        )
        self.compensation = apply_compensation(
            debt_id=self.jantar_debt.pk,
            reciprocal_debt_id=self.almoco_debt.pk,
            actor=self.ana,
            amount_cents=1_000,
            request_id=uuid4(),
        )

    def create_debt(self, *, debtor, creditor, title, total_cents):
        charge = create_charge(
            creator=debtor,
            title=title,
            total_cents=total_cents,
            invitee_ids=[],
            creditor_id=creditor.pk,
        )
        return charge, Debt.objects.get(participation__charge=charge)

    def test_dashboard_and_open_extracts_reconcile_across_several_charges(self):
        self.client.force_login(self.ana)

        payable = self.client.get(reverse("extracts:payable"))
        receivable = self.client.get(reverse("extracts:receivable"))
        dashboard = self.client.get(reverse("home"))

        assert payable.status_code == receivable.status_code == 200
        assert payable.context["total_cents"] == 14_500
        assert receivable.context["total_cents"] == 13_000
        assert dashboard.context["payable_cents"] == 14_500
        assert dashboard.context["receivable_cents"] == 13_000
        assert dashboard.context["paid_cents"] == 3_500

        bruno_group = next(
            group for group in payable.context["results"] if group.name == "Bruno"
        )
        assert bruno_group.total_cents == 11_500
        assert {debt.pk for debt in bruno_group.debts} == {
            self.jantar_debt.pk,
            self.uber_debt.pk,
        }
        assert (
            self.client.get(
                reverse("extracts:payable"),
                {"q": "Uber de Ana"},
            ).context["total_cents"]
            == 5_000
        )
        self.assertContains(payable, reverse("charges:detail", args=[self.jantar.pk]))
        self.assertContains(payable, "Jantar de Ana para Bruno")
        self.assertContains(receivable, "Cinema de Carla para Ana")
        self.assertNotContains(payable, "Cinema de Carla para Ana")

    def test_paid_timeline_filters_events_and_exports_csv_and_pdf(self):
        self.client.force_login(self.ana)
        local_today = timezone.localdate().isoformat()

        response = self.client.get(
            reverse("extracts:paid"),
            {"q": "Jantar", "date_from": local_today, "date_to": local_today},
        )

        assert response.status_code == 200
        assert response.context["total_cents"] == 3_500
        assert {event.event_type for event in response.context["results"]} == {
            "payment",
            "compensation",
        }

        csv_response = self.client.get(
            reverse("extracts:export_csv", args=["paid"]),
            {"page": "99"},
        )
        assert csv_response.status_code == 200
        assert csv_response["Content-Type"].startswith("text/csv")
        csv_content = csv_response.content.decode("utf-8-sig")
        assert f"payment:{self.confirmed_payment.pk}" in csv_content
        assert f"compensation:{self.compensation.request_id}" in csv_content
        assert f"payment:{self.pending_payment.pk}" not in csv_content
        assert "2500" in csv_content
        assert "1000" in csv_content

        pdf_response = self.client.get(
            reverse("extracts:export_pdf", args=["paid"]),
        )
        assert pdf_response.status_code == 200
        assert pdf_response["Content-Type"] == "application/pdf"
        assert pdf_response.content.startswith(b"%PDF-")

    def test_confirmed_payment_from_cancelled_charge_remains_audit_visible(self):
        charge, debt = self.create_debt(
            debtor=self.ana,
            creditor=self.carla,
            title="Ingresso cancelado",
            total_cents=2_000,
        )
        payment = record_payment(
            debt_id=debt.pk,
            actor=self.ana,
            amount_cents=700,
        )
        confirm_payment(payment_id=payment.pk, actor=self.carla)
        cancel_charge(charge_id=charge.pk, actor=self.ana)

        self.client.force_login(self.ana)
        response = self.client.get(reverse("extracts:paid"))

        revoked_event = next(
            event
            for event in response.context["results"]
            if event.event_id == f"payment:{payment.pk}"
        )
        assert revoked_event.state == "REVOKED"
        assert revoked_event.effective_at is not None
        assert response.context["total_cents"] == 3_500

    def test_extracts_do_not_disclose_charges_to_a_nonfinancial_creator(self):
        charge = create_charge(
            creator=self.diego,
            title="Cobrança criada por terceiro",
            total_cents=4_000,
            invitee_ids=[self.ana.pk],
            creditor_id=self.carla.pk,
            include_creator=False,
        )
        participation = charge.participations.get(user=self.ana)
        accept_participation(participation_id=participation.pk, actor=self.ana)

        self.client.force_login(self.diego)
        for route in ("extracts:payable", "extracts:receivable", "extracts:paid"):
            response = self.client.get(reverse(route))
            assert response.status_code == 200
            self.assertNotContains(response, charge.title)

        export = self.client.get(reverse("extracts:export_csv", args=["receivable"]))
        assert export.status_code == 200
        assert charge.title.encode() not in export.content

        self.client.logout()
        response = self.client.get(reverse("extracts:payable"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
