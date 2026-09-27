# ruff: noqa: PLR2004

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.services import accept_participation
from pixu.charges.services import cancel_charge
from pixu.charges.services import create_charge
from pixu.settlements.services import apply_compensation
from pixu.settlements.services import confirm_payment
from pixu.settlements.services import record_payment

User = get_user_model()


class ProductEntryTests(TestCase):
    def test_public_home_shows_landing_and_does_not_expose_private_charge(self):
        owner = User.objects.create_user(username="private-owner")
        Charge.objects.create(
            creator=owner,
            creditor=owner,
            title="PRIVATE DASHBOARD CHARGE",
            total_cents=9_900,
            state=Charge.State.ACTIVE,
        )

        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        self.assertContains(response, "Combinar o rateio fica mais simples.")
        self.assertContains(response, reverse("account_signup"))
        self.assertContains(response, reverse("account_login"))
        self.assertNotContains(response, "PRIVATE DASHBOARD CHARGE")

    def test_public_landing_describes_three_real_product_sections(self):
        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        self.assertContains(response, 'data-landing-section="rateio"')
        self.assertContains(response, 'data-landing-section="pagamentos"')
        self.assertContains(response, 'data-landing-section="historico"')
        content = response.content.decode().lower()
        assert content.count("data-landing-section=") == 3
        assert "demonstração" not in content
        assert "demo" not in content
        self.assertContains(response, "O Pix acontece fora.")
        self.assertContains(response, "confirma ou rejeita manualmente")
        self.assertContains(response, "quem a criou pode cancelá-la")

    def test_charge_list_requires_authentication(self):
        response = self.client.get(reverse("charges:list"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))

    def test_authenticated_home_renders_dashboard_and_charge_list_separately(self):
        user = User.objects.create_user(username="dashboard-user")
        self.client.force_login(user)

        dashboard_response = self.client.get(reverse("home"))
        charges_response = self.client.get(reverse("charges:list"))

        assert dashboard_response.status_code == 200
        self.assertContains(dashboard_response, "Potencial de compensação")
        self.assertContains(dashboard_response, "Você não tem convites pendentes.")
        assert charges_response.status_code == 200
        self.assertContains(charges_response, "Suas cobranças")


class DashboardBalanceTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(username="ana-dashboard")
        self.bruno = User.objects.create_user(username="bruno-dashboard")

    def create_active_debt(self, *, debtor, creditor, total_cents, title):
        charge = create_charge(
            creator=creditor,
            creditor_id=creditor.pk,
            title=title,
            total_cents=total_cents,
            invitee_ids=[debtor.pk],
            include_creator=False,
        )
        participation = charge.participations.get(user=debtor)
        accept_participation(participation_id=participation.pk, actor=debtor)
        return charge, Debt.objects.get(participation=participation)

    def test_dashboard_shows_open_totals_and_separate_net_compensation_potential(self):
        _charge, debt_to_bruno = self.create_active_debt(
            debtor=self.ana,
            creditor=self.bruno,
            total_cents=10_000,
            title="Jantar de Ana para Bruno",
        )
        _reverse_charge, debt_to_ana = self.create_active_debt(
            debtor=self.bruno,
            creditor=self.ana,
            total_cents=8_000,
            title="Cinema de Bruno para Ana",
        )
        confirmed = record_payment(
            debt_id=debt_to_bruno.pk,
            actor=self.ana,
            amount_cents=3_000,
        )
        confirm_payment(payment_id=confirmed.pk, actor=self.bruno)
        record_payment(debt_id=debt_to_bruno.pk, actor=self.ana, amount_cents=1_000)
        apply_compensation(
            debt_id=debt_to_bruno.pk,
            reciprocal_debt_id=debt_to_ana.pk,
            actor=self.ana,
            amount_cents=2_000,
            request_id=uuid.uuid4(),
        )
        pending_charge = create_charge(
            creator=self.ana,
            title="Cobrança ainda aguardando aceite",
            total_cents=40_000,
            invitee_ids=[self.bruno.pk],
        )
        assert pending_charge.state == Charge.State.AWAITING_ACCEPTANCE

        self.client.force_login(self.ana)
        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        assert response.context["payable_cents"] == 5_000
        assert response.context["receivable_cents"] == 6_000
        assert response.context["compensation_potential_cents"] == 4_000

    def test_dashboard_lists_pending_invites_and_other_people_charges(self):
        charge = create_charge(
            creator=self.bruno,
            title="Convite para Ana",
            total_cents=12_000,
            invitee_ids=[self.ana.pk],
            include_creator=False,
        )
        self.client.force_login(self.ana)

        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        assert list(response.context["pending_invites"]) == list(
            charge.participations.filter(user=self.ana),
        )
        assert list(response.context["participated_charges"]) == [charge]
        self.assertContains(response, "Convite para Ana")
        self.assertContains(response, "Cobranças de que você participa")

    def test_cancelled_charge_is_history_but_not_a_pending_invite_or_balance(self):
        charge, debt = self.create_active_debt(
            debtor=self.ana,
            creditor=self.bruno,
            total_cents=12_000,
            title="Rateio cancelado",
        )
        record_payment(
            debt_id=debt.pk,
            actor=self.ana,
            amount_cents=3_000,
        )
        cancel_charge(charge_id=charge.pk, actor=self.bruno)
        self.client.force_login(self.ana)

        response = self.client.get(reverse("home"))

        assert response.status_code == 200
        assert response.context["payable_cents"] == 0
        assert response.context["receivable_cents"] == 0
        assert response.context["compensation_potential_cents"] == 0
        assert list(response.context["pending_invites"]) == []
        assert list(response.context["participated_charges"]) == [charge]
        self.assertContains(response, "Rateio cancelado")
        self.assertContains(response, "Cancelada")
