# ruff: noqa: S105

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from pixu.accounts.models import PixProfile, User
from pixu.charges.models import Charge, Debt, Participation
from pixu.charges.services import calculate_itemized_shares
from pixu.charges.services import close_guest_entries
from pixu.charges.services import confirm_guest_participation
from pixu.charges.services import create_charge
from pixu.charges.services import enter_guest_charge
from pixu.charges.services import get_guest_participation
from pixu.charges.services import leave_guest_participation
from pixu.settlements.models import Payment
from pixu.settlements.services import confirm_payment
from pixu.settlements.services import record_payment


class GuestInviteServiceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="criador")
        PixProfile.objects.create(user=self.creator, pix_key="creator@example.test")

    def create_guest_charge(self, **options):
        return create_charge(
            creator=self.creator,
            title="Conta compartilhada",
            total_cents=47000,
            invitee_ids=[],
            guest_invites_enabled=True,
            **options,
        )

    def create_fixed_guest_charge(self, total_participants=2, **options):
        return self.create_guest_charge(
            guest_total_participants=total_participants,
            **options,
        )

    def test_guest_entry_is_dynamic_and_duplicate_names_get_distinct_codes(self):
        charge = self.create_guest_charge()
        credentials = charge._guest_credentials

        first = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Meireles",
        )
        second = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Meireles",
        )

        assert first.code != second.code
        assert first.participation.guest_name == "Meireles"
        assert second.participation.guest_name_normalized == "meireles"
        assert Participation.objects.get(pk=first.participation.pk).share_cents == 15667
        assert Participation.objects.get(pk=second.participation.pk).share_cents == 15666
        assert sum(charge.participations.values_list("share_cents", flat=True)) == 47000

    def test_close_confirm_and_guest_payment(self):
        charge = self.create_guest_charge()
        credentials = charge._guest_credentials
        access = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Ruan",
        )
        close_guest_entries(charge_id=charge.pk, actor=self.creator)
        confirm_guest_participation(
            participation_id=access.participation.pk,
            personal_code=access.code,
            expected_share_cents=23500,
            expected_creditor_id=self.creator.pk,
        )

        debt = Debt.objects.get(participation=access.participation)
        charge.refresh_from_db()
        assert charge.state == Charge.State.ACTIVE
        assert debt.debtor_id is None
        payment = record_payment(
            debt_id=debt.pk,
            actor=None,
            guest_participation_id=access.participation.pk,
            guest_code=access.code,
            amount_cents=23500,
        )
        assert payment.payer_id is None
        confirm_payment(payment_id=payment.pk, actor=self.creator)
        with pytest.raises(PermissionDenied):
            get_guest_participation(
                participation_id=access.participation.pk,
                personal_code=access.code,
            )

    def test_fixed_total_keeps_quota_stable_and_allows_payment_before_close(self):
        charge = self.create_fixed_guest_charge(total_participants=4)
        credentials = charge._guest_credentials
        first = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Primeira pessoa",
        )
        second = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Segunda pessoa",
        )

        first.participation.refresh_from_db()
        second.participation.refresh_from_db()
        assert first.participation.share_cents == 11750
        assert second.participation.share_cents == 11750

        confirm_guest_participation(
            participation_id=first.participation.pk,
            personal_code=first.code,
            expected_share_cents=11750,
            expected_creditor_id=self.creator.pk,
        )
        charge.refresh_from_db()
        assert charge.guest_entries_open is True
        assert charge.state == Charge.State.ACTIVE

        # The second guest may remain pending; the fixed denominator makes the
        # first accepted guest payable without closing the shared link.
        debt = Debt.objects.get(participation=first.participation)
        payment = record_payment(
            debt_id=debt.pk,
            actor=None,
            guest_participation_id=first.participation.pk,
            guest_code=first.code,
            amount_cents=11750,
        )
        assert payment.amount_cents == 11750

    def test_fixed_total_rejects_entries_after_declared_people_are_filled(self):
        charge = self.create_fixed_guest_charge(total_participants=2)
        credentials = charge._guest_credentials
        enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Pessoa",
        )
        with pytest.raises(ValidationError, match="total de participantes"):
            enter_guest_charge(
                charge_id=charge.pk,
                shared_secret=credentials["token"],
                name="Outra pessoa",
            )

    def test_guest_link_cannot_enter_after_close_and_can_leave_before_close(self):
        charge = self.create_guest_charge()
        credentials = charge._guest_credentials
        access = enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Pessoa",
        )
        leave_guest_participation(
            participation_id=access.participation.pk,
            personal_code=access.code,
        )
        assert Participation.objects.get(pk=access.participation.pk).state == Participation.State.CANCELLED
        with pytest.raises(ValidationError):
            close_guest_entries(charge_id=charge.pk, actor=self.creator)
        enter_guest_charge(
            charge_id=charge.pk,
            shared_secret=credentials["token"],
            name="Outra pessoa",
        )
        close_guest_entries(charge_id=charge.pk, actor=self.creator)
        with pytest.raises(PermissionDenied):
            enter_guest_charge(
                charge_id=charge.pk,
                shared_secret=credentials["token"],
                name="Mais uma pessoa",
            )

    def test_itemized_calculation_keeps_exact_total(self):
        values = calculate_itemized_shares(
            100,
            [3, 7, 9],
            [{"participation_id": 7, "amount_cents": 20}],
        )
        assert values[3]["share_cents"] == 27
        assert values[7]["share_cents"] == 47
        assert values[9]["share_cents"] == 26
        assert sum(item["share_cents"] for item in values.values()) == 100

        with pytest.raises(ValidationError):
            calculate_itemized_shares(10, [1], [{"participation_id": 1, "amount_cents": 11}])

    def test_public_entry_and_personal_page_are_server_rendered(self):
        charge = self.create_guest_charge()
        credentials = charge._guest_credentials
        entry_url = reverse("charges:guest_entry", args=[charge.pk, credentials["token"]])
        response = self.client.get(entry_url)
        assert response.status_code == 200
        response = self.client.post(entry_url, {"name": "Convidado web"})
        assert response.status_code == 200
        access = Participation.objects.get(charge=charge, guest_name="Convidado web")
        personal_url = reverse(
            "charges:guest_personal",
            args=[charge.pk, access.pk, response.context["personal_code"]],
        )
        personal = self.client.get(personal_url)
        assert personal.status_code == 200
        assert "Convidado web" in personal.content.decode()

    def test_authenticated_entry_is_bound_to_account_without_username_conflict(self):
        account = User.objects.create_user(username="meireles", name="Meireles")
        charge = self.create_guest_charge()
        credentials = charge._guest_credentials
        self.client.force_login(account)
        response = self.client.post(
            reverse("charges:guest_entry", args=[charge.pk, credentials["token"]]),
            {"name": "Meireles"},
        )
        assert response.status_code == 200
        participation = Participation.objects.get(charge=charge, user=account)
        assert participation.guest_name is None
        assert participation.guest_access_digest
