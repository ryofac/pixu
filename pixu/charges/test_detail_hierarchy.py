from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from pixu.charges.detail_context import charge_detail_context
from pixu.charges.models import Charge
from pixu.charges.models import ChargeItem
from pixu.charges.models import Debt
from pixu.charges.models import Participation
from pixu.settlements.models import Compensation
from pixu.settlements.models import Payment

User = get_user_model()


class ChargeDetailHierarchyTests(TestCase):
    def setUp(self):
        self.receiver = User.objects.create_user(
            username="recebedor",
            password="secret",
        )
        self.pending_payer = User.objects.create_user(
            username="ana-pendente",
            password="secret",
        )
        self.open_payer = User.objects.create_user(
            username="meireles-aberto",
            password="secret",
        )
        self.partial_payer = User.objects.create_user(
            username="bruno-parcial",
            password="secret",
        )
        self.charge = Charge.objects.create(
            creator=self.receiver,
            creditor=self.receiver,
            title="Almoço de teste",
            total_cents=50_000,
            state=Charge.State.ACTIVE,
        )
        self.own_participation = Participation.objects.create(
            charge=self.charge,
            user=self.receiver,
            share_cents=10_000,
            base_share_cents=10_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        self.pending_participation, self.pending_debt = self._accepted_debt(
            self.pending_payer,
            10_000,
        )
        self.pending_participation.base_share_cents = 9_000
        self.pending_participation.share_cents = 9_500
        self.pending_participation.save(
            update_fields=["base_share_cents", "share_cents"],
        )
        self.pending_debt.original_cents = 9_500
        self.pending_debt.save(update_fields=["original_cents"])
        self.open_participation, self.open_debt = self._accepted_debt(
            self.open_payer,
            10_000,
        )
        self.partial_participation, self.partial_debt = self._accepted_debt(
            self.partial_payer,
            10_000,
        )
        self.guest_participation = Participation.objects.create(
            charge=self.charge,
            guest_name="convidado-com-conta",
            guest_name_normalized="convidado-com-conta",
            guest_access_digest="TOKEN-PESSOAL-QUE-NAO-PODE-APARECER",
            share_cents=10_000,
            base_share_cents=10_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        self.guest_debt = Debt.objects.create(
            participation=self.guest_participation,
            debtor=None,
            creditor=self.receiver,
            original_cents=10_000,
        )
        Payment.objects.create(
            debt=self.pending_debt,
            payer=self.pending_payer,
            creditor=self.receiver,
            amount_cents=4_000,
            state=Payment.State.PENDING,
        )
        self.second_pending_payment = Payment.objects.create(
            debt=self.pending_debt,
            payer=self.pending_payer,
            creditor=self.receiver,
            amount_cents=1_000,
            state=Payment.State.PENDING,
        )
        ChargeItem.objects.create(
            charge=self.charge,
            participation=self.pending_participation,
            description="Sobremesa especial",
            amount_cents=500,
        )
        Payment.objects.create(
            debt=self.partial_debt,
            payer=self.partial_payer,
            creditor=self.receiver,
            amount_cents=2_000,
            state=Payment.State.CONFIRMED,
        )
        Payment.objects.create(
            debt=self.guest_debt,
            payer=None,
            creditor=self.receiver,
            amount_cents=10_000,
            state=Payment.State.CONFIRMED,
        )
        inverse_charge = Charge.objects.create(
            creator=self.partial_payer,
            creditor=self.partial_payer,
            title="Cobrança inversa",
            total_cents=3_000,
            state=Charge.State.ACTIVE,
        )
        inverse_participation = Participation.objects.create(
            charge=inverse_charge,
            user=self.receiver,
            share_cents=3_000,
            base_share_cents=3_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        inverse_debt = Debt.objects.create(
            participation=inverse_participation,
            debtor=self.receiver,
            creditor=self.partial_payer,
            original_cents=3_000,
        )
        Compensation.objects.create(
            debt=self.partial_debt,
            reciprocal_debt=inverse_debt,
            amount_cents=3_000,
            initiated_by=self.partial_payer,
        )
        self.open_debt.created_at = timezone.now() - timedelta(days=8)
        self.open_debt.save(update_fields=["created_at"])

    def _accepted_debt(self, user, share_cents, *, creditor=None):
        participation = Participation.objects.create(
            charge=self.charge,
            user=user,
            share_cents=share_cents,
            base_share_cents=share_cents,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        debt = Debt.objects.create(
            participation=participation,
            debtor=user,
            creditor=creditor or self.receiver,
            original_cents=share_cents,
        )
        return participation, debt

    def test_receiver_context_batches_balances_and_orders_identity_groups(self):
        with CaptureQueriesContext(connection) as queries:
            context = charge_detail_context(self.charge, self.receiver)

        # The receiver's rows use the same bounded set of query types;
        # balance calculation does not issue a query for each participation.
        assert len(queries) <= 8
        pixu_group, guest_group = context["receiver_participant_groups"]
        assert pixu_group["title"] == "Contas Pixu"
        assert guest_group["title"] == "Convites Anônimos"
        assert [line.participation.pk for line in pixu_group["lines"]] == [
            self.own_participation.pk,
            self.pending_participation.pk,
            self.open_participation.pk,
            self.partial_participation.pk,
        ]
        assert [line.participation.pk for line in guest_group["lines"]] == [
            self.guest_participation.pk,
        ]

        pending_line = pixu_group["lines"][1]
        assert pending_line.debt.payment_balance.open_cents == 9_500
        assert pending_line.debt.payment_balance.pending_cents == 5_000
        assert pending_line.debt.payment_balance.available_cents == 4_500
        assert len(pending_line.pending_payments) == 2

        open_line = pixu_group["lines"][2]
        assert open_line.open_age_label == "Em aberto há 8 dias"
        partial_line = pixu_group["lines"][3]
        assert partial_line.open_age_label == ""
        assert partial_line.debt.payment_balance.open_cents == 5_000
        assert partial_line.debt.payment_balance.confirmed_cents == 2_000
        assert partial_line.debt.payment_balance.compensated_cents == 3_000
        assert guest_group["lines"][0].debt.payment_balance.open_cents == 0

    def test_receiver_detail_renders_each_identity_once_without_guest_credentials(self):
        User.objects.create_user(username="convidado-com-conta", password="secret")
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert content.count('data-participant-row="') == 5
        assert "Contas Pixu" in content
        assert "Convites Anônimos" in content
        assert "Usuário externo" not in content
        assert ">Conta Pixu</span>" not in content
        assert "Pagamentos que precisam de atenção aparecerão primeiro" in content
        assert "Pessoas são agrupadas pela origem." not in content
        assert "TOKEN-PESSOAL-QUE-NAO-PODE-APARECER" not in content
        assert reverse("accounts:detail", args=["convidado-com-conta"]) not in content
        assert "Em aberto há 8 dias" in content
        assert "Cota quitada por Pix confirmado." in content
        assert "atrasad" not in content.lower()
        assert "venciment" not in content.lower()
        assert (
            "Sua participação no rateio não gera uma cobrança contra você."
            in content
        )
        assert content.count("Confirmar recebimento") == 2
        assert content.count('aria-label="Composição da cota"') == 1
        assert "Sobremesa especial" in content
        assert "R$ 90,00" in content
        assert "R$ 5,00" in content
        assert "R$ 95,00" in content
        assert "Pix pendente" in content
        assert "Em aberto" in content
        assert "Quitada" in content
        assert 'class="flex justify-start"' in content
        assert (
            reverse("settlements:confirm", args=[self.second_pending_payment.pk])
            in content
        )
        assert "Pagamentos e saldos" not in content

    def test_registered_identities_in_charge_detail_link_to_user_profiles(self):
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert (
            f'href="{reverse("accounts:detail", args=[self.receiver.username])}"'
            in content
        )
        assert (
            f'href="{reverse("accounts:detail", args=[self.pending_payer.username])}"'
            in content
        )
        assert (
            f'href="{reverse("accounts:detail", args=[self.open_payer.username])}"'
            in content
        )
        assert "convidado-com-conta" in content
        assert reverse("accounts:detail", args=["convidado-com-conta"]) not in content

    def test_receiver_detail_itemizes_share_with_each_extra_and_keeps_plain_share_concise(
        self,
    ):
        itemized_payer = User.objects.create_user(
            username="pagador-itemizado",
            password="secret",
        )
        itemized_participation, _debt = self._accepted_debt(itemized_payer, 9_600)
        itemized_participation.base_share_cents = 8_500
        itemized_participation.save(update_fields=["base_share_cents"])
        ChargeItem.objects.create(
            charge=self.charge,
            participation=itemized_participation,
            description="Bebida especial",
            amount_cents=500,
        )
        ChargeItem.objects.create(
            charge=self.charge,
            participation=itemized_participation,
            description="Taxa individual",
            amount_cents=600,
        )
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        itemized_row = content.split(
            f'data-participant-row="{itemized_participation.pk}"',
            1,
        )[1].split("</article>", 1)[0]
        assert 'data-share-composition="itemized"' in itemized_row
        composition = itemized_row.split(
            'data-share-composition="itemized"',
            1,
        )[1].split("</div>", 1)[0]
        assert "R$ 85,00" in composition
        assert composition.count("R$ 5,00") == 1
        assert composition.count("R$ 6,00") == 1
        assert composition.count("item extra") == 2
        assert "R$ 96,00" in composition
        assert "bg-pixu-surface-raised/70" in itemized_row
        assert 'class="flex justify-start"' in itemized_row
        assert "Detalhes e histórico" in itemized_row

        plain_row = content.split(
            f'data-participant-row="{self.open_participation.pk}"',
            1,
        )[1].split("</article>", 1)[0]
        assert 'data-share-composition="itemized"' not in plain_row
        assert "R$ 100,00" in plain_row
        assert "item extra" not in plain_row

    def test_nonreceiver_keeps_existing_payment_reading_without_decision_actions(self):
        self.client.force_login(self.pending_payer)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Pagamentos e saldos" in content
        assert "Participantes e cotas" not in content
        assert "Confirmar recebimento" not in content
        assert "Rejeitar pagamento" not in content

    def test_creator_who_is_not_receiver_does_not_gain_payment_decisions(self):
        creator = User.objects.create_user(
            username="criador-sem-recebimento",
            password="secret",
        )
        payer = User.objects.create_user(
            username="pagador-do-criador",
            password="secret",
        )
        charge = Charge.objects.create(
            creator=creator,
            creditor=self.receiver,
            title="Criador só acompanha",
            total_cents=1_000,
            state=Charge.State.ACTIVE,
        )
        participation = Participation.objects.create(
            charge=charge,
            user=payer,
            share_cents=1_000,
            base_share_cents=1_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        debt = Debt.objects.create(
            participation=participation,
            debtor=payer,
            creditor=self.receiver,
            original_cents=1_000,
        )
        Payment.objects.create(
            debt=debt,
            payer=payer,
            creditor=self.receiver,
            amount_cents=1_000,
            state=Payment.State.PENDING,
        )
        self.client.force_login(creator)

        response = self.client.get(reverse("charges:detail", args=[charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Participantes e cotas" not in content
        assert "Confirmar recebimento" not in content
        assert "Rejeitar pagamento" not in content

    def test_receiver_sees_pix_and_compensation_as_distinct_quit_methods(self):
        payer = User.objects.create_user(
            username="pagador-compensado",
            password="secret",
        )
        charge = Charge.objects.create(
            creator=self.receiver,
            creditor=self.receiver,
            title="Quitações distintas",
            total_cents=1_000,
            state=Charge.State.ACTIVE,
        )
        participation = Participation.objects.create(
            charge=charge,
            user=payer,
            share_cents=1_000,
            base_share_cents=1_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        debt = Debt.objects.create(
            participation=participation,
            debtor=payer,
            creditor=self.receiver,
            original_cents=1_000,
        )
        inverse_charge = Charge.objects.create(
            creator=self.receiver,
            creditor=payer,
            title="Crédito para compensar",
            total_cents=1_000,
            state=Charge.State.ACTIVE,
        )
        inverse_participation = Participation.objects.create(
            charge=inverse_charge,
            user=self.receiver,
            share_cents=1_000,
            base_share_cents=1_000,
            state=Participation.State.ACCEPTED,
            accepted_at=timezone.now(),
        )
        inverse_debt = Debt.objects.create(
            participation=inverse_participation,
            debtor=self.receiver,
            creditor=payer,
            original_cents=1_000,
        )
        Compensation.objects.create(
            debt=debt,
            reciprocal_debt=inverse_debt,
            amount_cents=1_000,
            initiated_by=payer,
        )
        self.client.force_login(self.receiver)

        response = self.client.get(reverse("charges:detail", args=[charge.pk]))

        assert response.status_code == 200
        assert "Cota quitada por compensação." in response.content.decode()
