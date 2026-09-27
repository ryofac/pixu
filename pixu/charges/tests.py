# ruff: noqa: PLR2004, S105

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import close_old_connections
from django.db import transaction
from django.test import Client
from django.test import TestCase
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.models import Participation
from pixu.charges.services import accept_participation
from pixu.charges.services import calculate_shares
from pixu.charges.services import create_charge
from pixu.charges.services import decline_participation
from pixu.charges.services import edit_participation_shares
from pixu.charges.services import replace_declined_participant

User = get_user_model()
TEST_PASSWORD = "Pixu-tests-only!2026"


class ChargeServiceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="ana", password=TEST_PASSWORD)
        self.bob = User.objects.create_user(username="bruno", password=TEST_PASSWORD)
        self.carla = User.objects.create_user(username="carla", password=TEST_PASSWORD)
        self.diego = User.objects.create_user(username="diego", password=TEST_PASSWORD)

    def create_charge(self, invitees=None, total_cents=10001):
        return create_charge(
            creator=self.creator,
            title="Jantar compartilhado",
            description="Conta do restaurante",
            total_cents=total_cents,
            invitee_ids=[user.pk for user in (invitees or [])],
        )

    def test_calculate_shares_distributes_remainder_by_sorted_user_id(self):
        shares = calculate_shares(1001, [self.carla.pk, self.creator.pk, self.bob.pk])

        assert shares == {self.creator.pk: 334, self.bob.pk: 334, self.carla.pk: 333}
        assert sum(shares.values()) == 1001

    def test_calculate_shares_rejects_empty_or_duplicate_participants(self):
        with pytest.raises(ValidationError):
            calculate_shares(100, [])
        with pytest.raises(ValidationError):
            calculate_shares(100, [self.bob.pk, self.bob.pk])

    def test_create_charge_splits_exactly_and_waits_for_invitees(self):
        charge = self.create_charge([self.bob, self.carla])
        participations = list(charge.participations.order_by("user_id"))

        assert charge.state == Charge.State.AWAITING_ACCEPTANCE
        assert charge.creditor_id == self.creator.pk
        assert sum(item.share_cents for item in participations) == charge.total_cents
        assert participations[0].user == self.creator
        assert participations[0].state == Participation.State.ACCEPTED
        assert Participation.objects.filter(charge=charge).count() == 3
        assert not Debt.objects.filter(participation__charge=charge).exists()

    def test_creator_only_charge_is_active_without_self_debt(self):
        charge = self.create_charge()

        assert charge.state == Charge.State.ACTIVE
        assert charge.participations.count() == 1
        assert not Debt.objects.filter(participation__charge=charge).exists()

    def test_creation_rejects_creator_as_invitee_and_unknown_user(self):
        with pytest.raises(ValidationError):
            create_charge(
                creator=self.creator,
                title="Cobrança",
                total_cents=100,
                invitee_ids=[self.creator.pk],
            )
        with pytest.raises(ValidationError):
            create_charge(
                creator=self.creator,
                title="Cobrança",
                total_cents=100,
                invitee_ids=[999999],
            )

    def test_acceptance_is_idempotent_and_activates_only_after_all_accept(self):
        charge = self.create_charge([self.bob, self.carla])
        bob_participation = charge.participations.get(user=self.bob)
        carla_participation = charge.participations.get(user=self.carla)

        accept_participation(participation_id=bob_participation.pk, actor=self.bob)
        accept_participation(participation_id=bob_participation.pk, actor=self.bob)
        charge.refresh_from_db()
        assert charge.state == Charge.State.AWAITING_ACCEPTANCE
        assert Debt.objects.filter(participation=bob_participation).count() == 1

        accept_participation(participation_id=carla_participation.pk, actor=self.carla)
        charge.refresh_from_db()
        assert charge.state == Charge.State.ACTIVE
        assert Debt.objects.filter(participation__charge=charge).count() == 2

    def test_only_invited_person_can_accept_or_decline(self):
        charge = self.create_charge([self.bob])
        invitation = charge.participations.get(user=self.bob)

        with pytest.raises(PermissionDenied):
            accept_participation(participation_id=invitation.pk, actor=self.carla)
        with pytest.raises(PermissionDenied):
            decline_participation(participation_id=invitation.pk, actor=self.carla)
        assert invitation.state == Participation.State.PENDING

    def test_decline_creates_no_debt_and_creator_can_replace_invitation(self):
        charge = self.create_charge([self.bob])
        declined = charge.participations.get(user=self.bob)

        declined = decline_participation(participation_id=declined.pk, actor=self.bob)
        replacement = replace_declined_participant(
            participation_id=declined.pk,
            replacement_user_id=self.carla.pk,
            actor=self.creator,
        )

        assert declined.state == Participation.State.DECLINED
        assert replacement.state == Participation.State.PENDING
        assert replacement.share_cents == declined.share_cents
        assert Debt.objects.filter(participation__charge=charge).count() == 0

    def test_only_creator_can_replace_declined_participant(self):
        charge = self.create_charge([self.bob])
        declined = decline_participation(
            participation_id=charge.participations.get(user=self.bob).pk,
            actor=self.bob,
        )

        with pytest.raises(PermissionDenied):
            replace_declined_participant(
                participation_id=declined.pk,
                replacement_user_id=self.carla.pk,
                actor=self.carla,
            )

    def test_creator_can_edit_own_and_pending_shares_but_not_accepted_share(self):
        charge = self.create_charge([self.bob, self.carla])
        bob_participation = charge.participations.get(user=self.bob)
        carla_participation = charge.participations.get(user=self.carla)
        accept_participation(participation_id=bob_participation.pk, actor=self.bob)

        shares = {
            item.pk: item.share_cents
            for item in charge.participations.exclude(
                state=Participation.State.DECLINED,
            )
        }
        shares[charge.participations.get(user=self.creator).pk] = 3000
        shares[carla_participation.pk] = (
            charge.total_cents - 3000 - bob_participation.share_cents
        )
        edit_participation_shares(
            charge_id=charge.pk,
            shares_by_participation=shares,
            actor=self.creator,
        )
        bob_participation.refresh_from_db()
        carla_participation.refresh_from_db()
        assert bob_participation.share_cents == shares[bob_participation.pk]
        assert carla_participation.share_cents == shares[carla_participation.pk]

        shares[bob_participation.pk] += 1
        shares[carla_participation.pk] -= 1
        with pytest.raises(ValidationError):
            edit_participation_shares(
                charge_id=charge.pk,
                shares_by_participation=shares,
                actor=self.creator,
            )

    def test_invalid_share_total_is_rejected_without_persistence(self):
        charge = self.create_charge([self.bob])
        original = list(charge.participations.values_list("pk", "share_cents"))
        shares = dict(original)
        shares[next(iter(shares))] += 1

        with pytest.raises(ValidationError):
            edit_participation_shares(
                charge_id=charge.pk,
                shares_by_participation=shares,
                actor=self.creator,
            )

        assert list(charge.participations.values_list("pk", "share_cents")) == original

    def test_database_constraints_reject_nonpositive_charge_total(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            Charge.objects.create(
                creator=self.creator,
                creditor=self.creator,
                title="Inválida",
                total_cents=0,
            )

        charge = self.create_charge([self.bob])
        with pytest.raises(IntegrityError), transaction.atomic():
            Participation.objects.create(
                charge=charge,
                user=self.bob,
                share_cents=charge.total_cents,
                state=Participation.State.PENDING,
            )

    def test_creator_can_be_excluded_with_manual_shares_and_external_creditor(self):
        charge = create_charge(
            creator=self.creator,
            title="Presente",
            total_cents=10001,
            invitee_ids=[self.bob.pk, self.carla.pk],
            creditor_id=self.diego.pk,
            include_creator=False,
            shares_by_user={self.bob.pk: 8000, self.carla.pk: 2001},
        )
        assert not charge.participations.filter(user=self.creator).exists()
        assert not charge.participations.filter(user=self.diego).exists()
        for person, value in [(self.bob, 8000), (self.carla, 2001)]:
            participation = charge.participations.get(user=person)
            accept_participation(participation_id=participation.pk, actor=person)
            debt = Debt.objects.get(participation=participation)
            assert debt.creditor == self.diego
            assert debt.original_cents == value
        charge.refresh_from_db()
        assert charge.state == Charge.State.ACTIVE

    def test_creator_owes_selected_creditor_but_creditor_never_owes_self(self):
        charge = create_charge(
            creator=self.creator,
            title="Jantar",
            total_cents=10000,
            invitee_ids=[self.bob.pk],
            creditor_id=self.bob.pk,
        )
        own_debt = Debt.objects.get(debtor=self.creator)
        assert own_debt.creditor == self.bob
        assert own_debt.original_cents == 5000
        accept_participation(
            participation_id=charge.participations.get(user=self.bob).pk,
            actor=self.bob,
        )
        assert Debt.objects.filter(participation__charge=charge).count() == 1

    def test_creation_rejects_invalid_participants_creditor_and_shares(self):
        self.diego.is_active = False
        self.diego.save(update_fields=["is_active"])
        invalid_options = [
            {"include_creator": False, "invitee_ids": []},
            {"creditor_id": self.diego.pk},
            {"creditor_id": 999999},
            {"shares_by_user": {self.creator.pk: 10000}},
            {"shares_by_user": {self.creator.pk: 5000, self.bob.pk: 4000}},
            {"shares_by_user": {self.creator.pk: -1, self.bob.pk: 10001}},
            {"shares_by_user": {self.creator.pk: True, self.bob.pk: 9999}},
        ]
        for options in invalid_options:
            with self.subTest(options=options):
                payload = {
                    "creator": self.creator,
                    "title": "Inválida",
                    "total_cents": 10000,
                    "invitee_ids": [self.bob.pk],
                    **options,
                }
                with pytest.raises(ValidationError):
                    create_charge(**payload)
                assert not Charge.objects.exists()
                assert not Participation.objects.exists()
                assert not Debt.objects.exists()

    def test_recipient_changes_and_own_share_changes_sync_creator_debt(self):
        charge = self.create_charge([self.bob], total_cents=10000)
        own = charge.participations.get(user=self.creator)
        invited = charge.participations.get(user=self.bob)
        shares = {own.pk: 4000, invited.pk: 6000}
        edit_participation_shares(
            charge_id=charge.pk,
            actor=self.creator,
            shares_by_participation=shares,
            creditor_id=self.carla.pk,
        )
        debt = Debt.objects.get(participation=own)
        assert debt.creditor == self.carla
        assert debt.original_cents == 4000
        shares[own.pk], shares[invited.pk] = 3000, 7000
        edit_participation_shares(
            charge_id=charge.pk,
            actor=self.creator,
            shares_by_participation=shares,
        )
        debt.refresh_from_db()
        assert debt.original_cents == 3000
        edit_participation_shares(
            charge_id=charge.pk,
            actor=self.creator,
            shares_by_participation=shares,
            creditor_id=self.creator.pk,
        )
        assert not Debt.objects.filter(participation=own).exists()

    def test_recipient_change_after_acceptance_is_rejected_atomically(self):
        charge = self.create_charge([self.bob, self.carla], total_cents=12000)
        accepted = charge.participations.get(user=self.bob)
        accept_participation(participation_id=accepted.pk, actor=self.bob)
        original = dict(charge.participations.values_list("pk", "share_cents"))
        modified = dict(original)
        modified[charge.participations.get(user=self.creator).pk] += 100
        modified[charge.participations.get(user=self.carla).pk] -= 100
        with pytest.raises(ValidationError, match="recebedor não pode mudar"):
            edit_participation_shares(
                charge_id=charge.pk,
                actor=self.creator,
                shares_by_participation=modified,
                creditor_id=self.diego.pk,
            )
        charge.refresh_from_db()
        assert charge.creditor == self.creator
        assert dict(charge.participations.values_list("pk", "share_cents")) == original
        assert accepted.debt.creditor == self.creator

    def test_financial_lock_blocks_recipient_and_share_edits(self):
        charge = self.create_charge([self.bob])
        charge.locked_at = timezone.now()
        charge.save(update_fields=["locked_at"])
        with pytest.raises(ValidationError, match="operação financeira"):
            edit_participation_shares(
                charge_id=charge.pk,
                actor=self.creator,
                shares_by_participation=dict(
                    charge.participations.values_list("pk", "share_cents"),
                ),
                creditor_id=self.carla.pk,
            )

    def test_acceptance_rejects_outdated_share_or_recipient(self):
        charge = self.create_charge([self.bob])
        participation = charge.participations.get(user=self.bob)
        for share, creditor in [
            (participation.share_cents + 1, charge.creditor_id),
            (participation.share_cents, self.carla.pk),
        ]:
            with pytest.raises(ValidationError, match="mudou"):
                accept_participation(
                    participation_id=participation.pk,
                    actor=self.bob,
                    expected_share_cents=share,
                    expected_creditor_id=creditor,
                )
        participation.refresh_from_db()
        assert participation.state == Participation.State.PENDING
        assert not Debt.objects.exists()


class ChargeViewTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="ana", password=TEST_PASSWORD)
        self.invitee = User.objects.create_user(
            username="bruno",
            password=TEST_PASSWORD,
        )
        self.outsider = User.objects.create_user(
            username="carla",
            password=TEST_PASSWORD,
        )
        self.charge = create_charge(
            creator=self.creator,
            title="Churrasco",
            description="Encontro do grupo",
            total_cents=10000,
            invitee_ids=[self.invitee.pk],
        )
        self.invitation = self.charge.participations.get(user=self.invitee)

    def acceptance_data(self):
        return {
            "expected_share_cents": self.invitation.share_cents,
            "expected_creditor_id": self.charge.creditor_id,
        }

    def creation_data(self):
        return {
            "title": "Cinema",
            "total": "100,00",
            "invitees": [self.invitee.pk],
            "creditor": self.creator.pk,
            "include_creator": "on",
        }

    def test_nonparticipant_cannot_open_charge_or_answer_invite(self):
        self.client.force_login(self.outsider)

        detail = self.client.get(reverse("charges:detail", args=[self.charge.pk]))
        accept = self.client.post(
            reverse("charges:accept", args=[self.charge.pk, self.invitation.pk]),
        )

        assert detail.status_code == 404
        assert accept.status_code == 404

    def test_hx_accept_returns_updated_fragment_and_updates_invite_badge(self):
        self.client.force_login(self.invitee)
        response = self.client.post(
            reverse("charges:accept", args=[self.charge.pk, self.invitation.pk]),
            self.acceptance_data(),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET=f"invite-{self.invitation.pk}",
        )

        assert response.status_code == 200
        self.assertContains(response, "Aceita")
        assert (
            response["HX-Trigger"] == '{"pixu:pending-invites-updated": {"count": 0}}'
        )

    def test_htmx_preview_calculates_shares_without_saving_charge(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("charges:preview"),
            {**self.creation_data(), "total": "100,01"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        self.assertContains(response, "Prévia do rateio")
        self.assertContains(response, "50,01")
        self.assertContains(response, "100,01")
        assert Charge.objects.count() == 1

    def test_money_input_accepts_pt_br_and_dotted_decimal_forms(self):
        self.client.force_login(self.creator)

        for value in ("150,00", "150.00"):
            response = self.client.post(
                reverse("charges:preview"),
                {**self.creation_data(), "total": value},
                HTTP_HX_REQUEST="true",
            )
            assert response.status_code == 200
            self.assertContains(response, "150,00")

        response = self.client.post(
            reverse("charges:preview"),
            {**self.creation_data(), "total": "not-money"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        self.assertContains(response, "Informe um número.")
        self.assertNotContains(response, "Enter a number")

    def test_create_form_has_registered_user_search_and_filters_only_preview_fields(
        self,
    ):
        self.client.force_login(self.creator)

        response = self.client.get(reverse("charges:create"))

        assert response.status_code == 200
        self.assertContains(response, "data-invitee-search")
        self.assertContains(response, "data-invitee-option")
        self.assertContains(
            response, 'hx-trigger="input changed delay:300ms from:input[name=total]',
        )

    def test_conventional_create_post_creates_charge_and_redirects(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse("charges:create"),
            {
                **self.creation_data(),
                "description": "Sessão de sábado",
            },
        )

        assert response.status_code == 302
        charge = Charge.objects.get(title="Cinema")
        assert charge.description == "Sessão de sábado"
        assert charge.total_cents == 10000
        assert charge.state == Charge.State.AWAITING_ACCEPTANCE

    def test_conventional_accept_post_redirects_to_charge(self):
        self.client.force_login(self.invitee)

        response = self.client.post(
            reverse("charges:accept", args=[self.charge.pk, self.invitation.pk]),
            self.acceptance_data(),
        )

        assert response.status_code == 302
        assert response.url == reverse("charges:detail", args=[self.charge.pk])
        assert Debt.objects.filter(participation=self.invitation).count() == 1

    def test_charge_description_is_escaped_in_detail(self):
        self.charge.description = "<script>alert('x')</script>"
        self.charge.save(update_fields=["description"])
        self.client.force_login(self.creator)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_create_charge_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.creator)

        response = csrf_client.post(
            reverse("charges:create"),
            {"title": "Cinema", "total": "100,00", "invitees": []},
        )

        assert response.status_code == 403

    def test_invalid_charge_form_does_not_persist(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse("charges:create"),
            {
                "title": "",
                "total": "0,00",
                "invitees": [self.invitee.pk],
            },
        )

        assert response.status_code == 200
        assert Charge.objects.count() == 1
        self.assertContains(response, "maior ou igual a 0.01")
        self.assertContains(response, 'aria-invalid="true"')

    def test_preview_without_javascript_and_create_preserves_manual_shares(self):
        self.client.force_login(self.creator)
        data = self.creation_data()
        response = self.client.post(
            reverse("charges:create"),
            {**data, "intent": "preview"},
        )
        self.assertContains(response, "Prévia do rateio")
        self.assertContains(response, f'name="share_{self.creator.pk}"')
        assert Charge.objects.count() == 1
        response = self.client.post(
            reverse("charges:create"),
            {
                **data,
                f"share_{self.creator.pk}": "20,00",
                f"share_{self.invitee.pk}": "80,00",
            },
        )
        assert response.status_code == 302
        charge = Charge.objects.get(title="Cinema")
        assert charge.participations.get(user=self.creator).share_cents == 2000
        assert charge.participations.get(user=self.invitee).share_cents == 8000

    def test_invalid_manual_shares_preserve_fields_without_saving(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("charges:create"),
            {
                **self.creation_data(),
                f"share_{self.creator.pk}": "20,00",
                f"share_{self.invitee.pk}": "90,00",
            },
        )
        self.assertContains(response, "A soma das cotas deve ser igual")
        self.assertContains(response, 'value="90,00"')
        assert Charge.objects.count() == 1

    def test_create_without_own_share_and_with_another_creditor(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("charges:create"),
            {
                **self.creation_data(),
                "include_creator": "",
                "creditor": self.outsider.pk,
                f"share_{self.invitee.pk}": "100,00",
            },
        )
        assert response.status_code == 302
        charge = Charge.objects.get(title="Cinema")
        assert charge.creator == self.creator
        assert charge.creditor == self.outsider
        assert charge.participations.count() == 1
        assert charge.participations.get().user == self.invitee

    def test_recipient_without_participation_can_read_but_cannot_edit(self):
        self.charge.creditor = self.outsider
        self.charge.save(update_fields=["creditor"])
        self.client.force_login(self.outsider)
        self.assertContains(
            self.client.get(reverse("charges:detail", args=[self.charge.pk])),
            "Churrasco",
        )
        self.assertContains(self.client.get(reverse("charges:list")), "Churrasco")
        response = self.client.post(
            reverse("charges:edit_shares", args=[self.charge.pk]),
            {"creditor": self.outsider.pk},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403

    def test_htmx_updates_recipient_then_rejects_stale_acceptance(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("charges:edit_shares", args=[self.charge.pk]),
            {
                "creditor": self.outsider.pk,
                **{
                    f"share_{item.pk}": "50,00"
                    for item in self.charge.participations.all()
                },
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(response, "Cotas e recebedor atualizados.")
        self.charge.refresh_from_db()
        assert self.charge.creditor == self.outsider
        self.client.force_login(self.invitee)
        response = self.client.post(
            reverse("charges:accept", args=[self.charge.pk, self.invitation.pk]),
            {
                "expected_share_cents": self.invitation.share_cents,
                "expected_creditor_id": self.creator.pk,
            },
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET=f"invite-{self.invitation.pk}",
        )
        self.assertContains(response, "O rateio ou o recebedor mudou")
        self.assertContains(response, "Quem recebe: carla")
        self.invitation.refresh_from_db()
        assert self.invitation.state == Participation.State.PENDING
        assert not Debt.objects.filter(participation=self.invitation).exists()

    def test_missing_consent_values_do_not_accept_invitation(self):
        self.client.force_login(self.invitee)
        self.client.post(
            reverse("charges:accept", args=[self.charge.pk, self.invitation.pk]),
        )
        self.invitation.refresh_from_db()
        assert self.invitation.state == Participation.State.PENDING


class ChargeConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.creator = User.objects.create_user(username="ana", password=TEST_PASSWORD)
        self.invitee = User.objects.create_user(
            username="bruno",
            password=TEST_PASSWORD,
        )
        self.charge = create_charge(
            creator=self.creator,
            title="Corrida de app",
            total_cents=5000,
            invitee_ids=[self.invitee.pk],
        )
        self.invitation_id = self.charge.participations.get(user=self.invitee).pk
        self.invitee_id = self.invitee.pk

    def test_concurrent_acceptance_creates_only_one_debt(self):
        start = Barrier(2)

        def accept_from_separate_connection():
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.invitee_id)
                start.wait(timeout=5)
                return accept_participation(
                    participation_id=self.invitation_id,
                    actor=actor,
                ).state
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(accept_from_separate_connection) for _ in range(2)]
            states = [future.result(timeout=15) for future in futures]

        assert states == [Participation.State.ACCEPTED, Participation.State.ACCEPTED]
        assert Debt.objects.filter(participation_id=self.invitation_id).count() == 1
        self.charge.refresh_from_db()
        assert self.charge.state == Charge.State.ACTIVE

    def test_acceptance_and_creditor_change_serialize_without_stale_consent(self):
        recipient = User.objects.create_user(username="carla", password=TEST_PASSWORD)
        shares = dict(self.charge.participations.values_list("pk", "share_cents"))
        expected_share = self.charge.participations.get(
            pk=self.invitation_id,
        ).share_cents
        start = Barrier(2)

        def act_from_separate_connection(action):
            close_old_connections()
            try:
                start.wait(timeout=5)
                if action == "accept":
                    accept_participation(
                        participation_id=self.invitation_id,
                        actor=self.invitee,
                        expected_creditor_id=self.creator.pk,
                        expected_share_cents=expected_share,
                    )
                else:
                    edit_participation_shares(
                        charge_id=self.charge.pk,
                        actor=self.creator,
                        shares_by_participation=shares,
                        creditor_id=recipient.pk,
                    )
            except ValidationError:
                return "conflict"
            else:
                return "saved"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(act_from_separate_connection, action)
                for action in ("accept", "change_creditor")
            ]
            results = [future.result(timeout=15) for future in futures]

        assert sorted(results) == ["conflict", "saved"]
        self.charge.refresh_from_db()
        assert (
            not Debt.objects.filter(participation__charge=self.charge)
            .exclude(
                creditor_id=self.charge.creditor_id,
            )
            .exists()
        )
        invitation = self.charge.participations.get(pk=self.invitation_id)
        if self.charge.creditor_id == recipient.pk:
            assert invitation.state == Participation.State.PENDING
            assert self.charge.state == Charge.State.AWAITING_ACCEPTANCE
        else:
            assert invitation.state == Participation.State.ACCEPTED
            assert self.charge.state == Charge.State.ACTIVE
