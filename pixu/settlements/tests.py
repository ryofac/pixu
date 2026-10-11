from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

# ruff: noqa: PLR2004, S105
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.db import connections
from django.test import Client
from django.test import TestCase
from django.test import TransactionTestCase
from django.urls import reverse

from pixu.accounts.models import PixProfile
from pixu.accounts.models import User
from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.charges.services import cancel_charge
from pixu.charges.services import create_charge
from pixu.charges.services import edit_participation_shares

from .models import Compensation
from .models import Payment
from .services import apply_compensation
from .services import confirm_payment
from .services import delete_receipt
from .services import payment_balance
from .services import record_payment
from .services import reject_payment
from .services import replace_receipt
from .services import set_debt_auto_confirm
from .services import suggest_compensations

TEST_PASSWORD = "Pixu-tests-only!2026"


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan",
            password=TEST_PASSWORD,
        )
        self.outsider = User.objects.create_user(
            username="bruno",
            password=TEST_PASSWORD,
        )
        PixProfile.objects.create(user=self.creditor, pix_key="ryan@example.test")
        self.charge = create_charge(
            creator=self.debtor,
            title="Churrasco",
            total_cents=10000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=self.charge)

    def test_record_payment_reserves_without_reducing_open_balance(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
            reference="Pix do almoço",
        )

        assert payment.state == Payment.State.PENDING
        assert payment.payer_id == self.debtor.pk
        assert payment.creditor_id == self.creditor.pk
        assert payment_balance(self.debt) == payment_balance(self.debt).__class__(
            original_cents=10000,
            confirmed_cents=0,
            compensated_cents=0,
            pending_cents=2000,
            open_cents=10000,
            available_cents=8000,
        )
        self.charge.refresh_from_db()
        assert self.charge.locked_at is not None

    def test_payment_balance_subtracts_compensation_on_both_sides(self):
        inverse_charge = create_charge(
            creator=self.creditor,
            title="Almoço",
            total_cents=7000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        inverse_debt = Debt.objects.get(participation__charge=inverse_charge)
        Compensation.objects.create(
            debt=self.debt,
            reciprocal_debt=inverse_debt,
            initiated_by=self.debtor,
            amount_cents=3000,
        )

        confirmed = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        confirm_payment(payment_id=confirmed.pk, actor=self.creditor)
        record_payment(debt_id=self.debt.pk, actor=self.debtor, amount_cents=1000)
        record_payment(debt_id=inverse_debt.pk, actor=self.creditor, amount_cents=500)

        assert payment_balance(self.debt) == payment_balance(self.debt).__class__(
            original_cents=10000,
            confirmed_cents=2000,
            compensated_cents=3000,
            pending_cents=1000,
            open_cents=5000,
            available_cents=4000,
        )
        assert payment_balance(inverse_debt) == payment_balance(
            inverse_debt,
        ).__class__(
            original_cents=7000,
            confirmed_cents=0,
            compensated_cents=3000,
            pending_cents=500,
            open_cents=4000,
            available_cents=3500,
        )

    def test_record_rejects_excess_and_non_debtor(self):
        with pytest.raises(ValidationError):
            record_payment(
                debt_id=self.debt.pk,
                actor=self.debtor,
                amount_cents=10001,
            )
        with pytest.raises(PermissionDenied):
            record_payment(
                debt_id=self.debt.pk,
                actor=self.outsider,
                amount_cents=100,
            )
        assert not Payment.objects.exists()

    def test_confirm_is_manual_audited_and_idempotent(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        with pytest.raises(PermissionDenied):
            confirm_payment(payment_id=payment.pk, actor=self.debtor)
        confirmed = confirm_payment(payment_id=payment.pk, actor=self.creditor)
        repeated = confirm_payment(payment_id=payment.pk, actor=self.creditor)

        assert confirmed.pk == repeated.pk == payment.pk
        assert confirmed.state == Payment.State.CONFIRMED
        assert confirmed.confirmed_by_id == self.creditor.pk
        assert confirmed.confirmed_at is not None
        assert confirmed.confirmation_source == Payment.ConfirmationSource.MANUAL
        assert payment_balance(self.debt).open_cents == 8000

    def test_auto_confirmation_is_audited_scoped_to_future_payments(self):
        enabled_debt = set_debt_auto_confirm(
            debt_id=self.debt.pk,
            actor=self.creditor,
            enabled=True,
        )
        automatic = record_payment(
            debt_id=enabled_debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )

        assert automatic.state == Payment.State.CONFIRMED
        assert automatic.confirmation_source == Payment.ConfirmationSource.AUTOMATIC
        assert automatic.confirmed_by_id is None
        assert automatic.confirmed_at is not None
        assert payment_balance(self.debt).open_cents == 8000

        set_debt_auto_confirm(
            debt_id=self.debt.pk,
            actor=self.creditor,
            enabled=False,
        )
        manual = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=1000,
        )
        assert manual.state == Payment.State.PENDING
        assert manual.confirmation_source == Payment.ConfirmationSource.MANUAL
        assert payment_balance(self.debt).open_cents == 8000
        assert payment_balance(self.debt).pending_cents == 1000

    def test_only_receiver_can_configure_auto_confirmation_for_active_account_debt(self):
        with pytest.raises(PermissionDenied):
            set_debt_auto_confirm(
                debt_id=self.debt.pk,
                actor=self.outsider,
                enabled=True,
            )

        self.charge.state = Charge.State.CANCELLED
        self.charge.save(update_fields=["state"])
        with pytest.raises(ValidationError):
            set_debt_auto_confirm(
                debt_id=self.debt.pk,
                actor=self.creditor,
                enabled=True,
            )

    def test_reject_releases_reservation_but_keeps_history(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        rejected = reject_payment(payment_id=payment.pk, actor=self.creditor)
        repeated = reject_payment(payment_id=payment.pk, actor=self.creditor)

        assert rejected.state == repeated.state == Payment.State.REJECTED
        assert rejected.rejected_by_id == self.creditor.pk
        assert payment_balance(self.debt).available_cents == 10000

    def test_database_constraint_accepts_revoked_payment_state(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=1000,
        )
        payment.state = Payment.State.REVOKED
        payment.save(update_fields=["state"])

        payment.refresh_from_db()
        assert payment.state == Payment.State.REVOKED

    def test_cancelling_charge_revokes_pending_payment_and_preserves_receipt(self):
        receipt = SimpleUploadedFile(
            "comprovante.pdf",
            b"%PDF-1.7\ncomprovante",
            content_type="application/pdf",
        )
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
            receipt=receipt,
        )
        receipt_name = payment.receipt.name

        cancel_charge(charge_id=self.charge.pk, actor=self.debtor, reason="Cancelada")

        payment.refresh_from_db()
        self.charge.refresh_from_db()
        assert self.charge.state == Charge.State.CANCELLED
        assert self.charge.cancellation_reason == "Cancelada"
        assert payment.state == Payment.State.REVOKED
        assert payment.receipt.name == receipt_name
        assert payment.receipt.storage.exists(receipt_name)
        assert payment_balance(self.debt).pending_cents == 0
        with pytest.raises(ValidationError):
            confirm_payment(payment_id=payment.pk, actor=self.creditor)
        with pytest.raises(ValidationError):
            reject_payment(payment_id=payment.pk, actor=self.creditor)
        with pytest.raises(ValidationError):
            record_payment(
                debt_id=self.debt.pk,
                actor=self.debtor,
                amount_cents=1000,
            )

    def test_cancelling_charge_revokes_confirmed_payment_without_removing_audit(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        confirm_payment(payment_id=payment.pk, actor=self.creditor)

        cancel_charge(charge_id=self.charge.pk, actor=self.debtor)

        payment.refresh_from_db()
        assert payment.state == Payment.State.REVOKED
        assert payment.confirmed_by_id == self.creditor.pk
        assert payment.confirmed_at is not None

    def test_rejected_payment_does_not_unlock_charge(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=1000,
        )
        reject_payment(payment_id=payment.pk, actor=self.creditor)
        shares = dict(self.charge.participations.values_list("pk", "share_cents"))
        with pytest.raises(ValidationError):
            edit_participation_shares(
                charge_id=self.charge.pk,
                shares_by_participation=shares,
                actor=self.debtor,
            )

    def test_receipt_is_private_and_validated(self):
        receipt = SimpleUploadedFile(
            "comprovante.pdf",
            b"%PDF-1.7\ncomprovante",
            content_type="application/pdf",
        )
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=1000,
            receipt=receipt,
        )
        assert payment.receipt.name.startswith("private_uploads/payments/")

        debtor_client = Client()
        debtor_client.force_login(self.debtor)
        response = debtor_client.get(reverse("settlements:receipt", args=[payment.pk]))
        assert response.status_code == 200
        assert response["Content-Disposition"].startswith("inline;")
        assert b"".join(response.streaming_content).startswith(b"%PDF")

        self.charge.creator = self.outsider
        self.charge.save(update_fields=["creator"])
        creator_client = Client()
        creator_client.force_login(self.outsider)
        creator_response = creator_client.get(
            reverse("settlements:receipt", args=[payment.pk]),
        )
        assert creator_response.status_code == 200
        assert creator_response["Content-Disposition"].startswith("inline;")
        assert creator_response["X-Content-Type-Options"] == "nosniff"
        assert creator_response["Cache-Control"] == "private, no-store"
        b"".join(creator_response.streaming_content)

        third_party = User.objects.create_user(
            username="third-party",
            password=TEST_PASSWORD,
        )
        outsider_client = Client()
        outsider_client.force_login(third_party)
        assert (
            outsider_client.get(
                reverse("settlements:receipt", args=[payment.pk]),
            ).status_code
            == 403
        )

        invalid = SimpleUploadedFile(
            "comprovante.pdf",
            b"not-a-pdf",
            content_type="application/pdf",
        )
        with pytest.raises(ValidationError):
            record_payment(
                debt_id=self.debt.pk,
                actor=self.debtor,
                amount_cents=1000,
                receipt=invalid,
            )

    def test_pending_receipt_can_be_replaced_and_deleted_by_payer(self):
        first = SimpleUploadedFile(
            "primeiro.pdf",
            b"%PDF-1.7\nprimeiro",
            content_type="application/pdf",
        )
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=1000,
            receipt=first,
        )
        old_name = payment.receipt.name
        replacement = SimpleUploadedFile(
            "segundo.pdf",
            b"%PDF-1.7\nsegundo",
            content_type="application/pdf",
        )
        payment = replace_receipt(
            payment_id=payment.pk,
            actor=self.debtor,
            receipt=replacement,
        )
        assert payment.receipt.name != old_name
        assert payment.state == Payment.State.PENDING
        assert payment.receipt_original_name == "segundo.pdf"

        delete_receipt(payment_id=payment.pk, actor=self.debtor)
        payment.refresh_from_db()
        assert not payment.receipt
        assert payment.receipt_size is None
        assert payment.state == Payment.State.PENDING

        with pytest.raises(PermissionDenied):
            replace_receipt(
                payment_id=payment.pk,
                actor=self.creditor,
                receipt=SimpleUploadedFile(
                    "terceiro.pdf",
                    b"%PDF-1.7\nterceiro",
                    content_type="application/pdf",
                ),
            )


class PaymentViewTests(TestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan",
            password=TEST_PASSWORD,
        )
        PixProfile.objects.create(user=self.creditor, pix_key="ryan@example.test")
        self.charge = create_charge(
            creator=self.debtor,
            title="Cinema",
            total_cents=5000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=self.charge)

    def test_debtor_sees_key_and_can_register_from_form(self):
        self.client.force_login(self.debtor)
        response = self.client.get(reverse("settlements:record", args=[self.debt.pk]))
        assert response.status_code == 200
        content = response.content.decode()
        assert "ryan@example.test" in content
        assert "Nenhum arquivo selecionado" in content
        assert 'data-file-input="true"' in content
        assert (
            'accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"'
            in content
        )

        response = self.client.post(
            reverse("settlements:record", args=[self.debt.pk]),
            {"amount": "20,00", "reference": "Ingresso"},
        )
        assert response.status_code == 302
        assert Payment.objects.get().amount_cents == 2000

    def test_payment_form_accepts_dotted_decimal_for_compatibility(self):
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse("settlements:record", args=[self.debt.pk]),
            {"amount": "20.00", "reference": "Ingresso"},
        )

        assert response.status_code == 302
        assert Payment.objects.get().amount_cents == 2000

    def test_payment_view_reports_immediate_automatic_confirmation(self):
        set_debt_auto_confirm(
            debt_id=self.debt.pk,
            actor=self.creditor,
            enabled=True,
        )
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse("settlements:record", args=[self.debt.pk]),
            {"amount": "20,00", "reference": "Ingresso"},
            follow=True,
        )

        assert response.status_code == 200
        assert "confirmado automaticamente no Pixu" in response.content.decode()

    def test_receiver_can_decide_over_htmx_and_detail_updates(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        self.client.force_login(self.creditor)
        response = self.client.post(
            reverse("settlements:confirm", args=[payment.pk]),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET=f"debt-{self.debt.pk}",
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert 'id="charge-content"' in content
        assert f'id="debt-{self.debt.pk}"' in content
        assert "Pagamento confirmado." in content
        assert "30,00" in content

    def test_receiver_can_set_auto_confirmation_over_htmx_but_debtor_cannot(self):
        self.client.force_login(self.creditor)
        response = self.client.post(
            reverse("settlements:auto_confirm", args=[self.debt.pk]),
            {"auto_confirm_payments": "on"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="charge-content",
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert 'name="auto_confirm_payments"' in content
        assert "O Pixu não verifica a transferência" in content
        self.debt.refresh_from_db()
        assert self.debt.auto_confirm_payments

        self.client.force_login(self.debtor)
        forbidden = self.client.post(
            reverse("settlements:auto_confirm", args=[self.debt.pk]),
            {"auto_confirm_payments": "on"},
            HTTP_HX_REQUEST="true",
        )
        assert forbidden.status_code == 403

    def test_htmx_rejection_and_validation_error_keep_the_full_charge_fragment(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        self.client.force_login(self.creditor)
        rejected = self.client.post(
            reverse("settlements:reject", args=[payment.pk]),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="charge-content",
        )

        assert rejected.status_code == 200
        assert 'id="charge-content"' in rejected.content.decode()
        assert "Pagamento rejeitado; o valor voltou a ficar disponível." in (
            rejected.content.decode()
        )

        invalid = self.client.post(
            reverse("settlements:confirm", args=[payment.pk]),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="charge-content",
        )

        assert invalid.status_code == 400
        invalid_content = invalid.content.decode()
        assert 'id="charge-content"' in invalid_content
        assert "Este pagamento não está mais pendente." in invalid_content

    def test_decision_view_keeps_csrf_and_receiver_authorization(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.creditor)
        csrf_response = csrf_client.post(
            reverse("settlements:confirm", args=[payment.pk]),
            HTTP_HX_REQUEST="true",
        )
        assert csrf_response.status_code == 403
        payment.refresh_from_db()
        assert payment.state == Payment.State.PENDING

        outsider = User.objects.create_user(
            username="terceiro-da-decisao",
            password=TEST_PASSWORD,
        )
        self.client.force_login(outsider)
        denied = self.client.post(
            reverse("settlements:confirm", args=[payment.pk]),
            HTTP_HX_REQUEST="true",
        )
        assert denied.status_code == 403
        payment.refresh_from_db()
        assert payment.state == Payment.State.PENDING

    def test_charge_detail_renders_pending_receipt_form(self):
        record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        self.client.force_login(self.debtor)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Substituir comprovante" in content
        assert "Nenhum arquivo selecionado" in content

    def test_invalid_receipt_update_keeps_debt_card(self):
        payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse("settlements:receipt_update", args=[payment.pk]),
            {},
            HTTP_HX_REQUEST="true",
        )

        content = response.content.decode()
        assert response.status_code == 400
        assert f'id="debt-{self.debt.pk}"' in content
        assert "Este campo é obrigatório" in content


class CompensationSuggestionTests(TestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana-compensacao",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan-compensacao",
            password=TEST_PASSWORD,
        )
        self.outsider = User.objects.create_user(
            username="bruno-compensacao",
            password=TEST_PASSWORD,
        )
        self.debt_charge = create_charge(
            creator=self.debtor,
            title="Jantar",
            total_cents=5000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=self.debt_charge)
        self.inverse_charge = create_charge(
            creator=self.creditor,
            title="Cinema",
            total_cents=3000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        self.inverse_debt = Debt.objects.get(
            participation__charge=self.inverse_charge,
        )
        inactive_charge = create_charge(
            creator=self.creditor,
            title="Viagem pendente",
            total_cents=6000,
            invitee_ids=[self.outsider.pk],
            creditor_id=self.debtor.pk,
        )
        self.inactive_inverse_debt = Debt.objects.get(
            participation__charge=inactive_charge,
        )

    def test_suggests_only_active_accepted_inverse_debts(self):
        options = suggest_compensations(debt_id=self.debt.pk, actor=self.debtor)

        assert len(options) == 1
        assert options[0].reciprocal_debt.pk == self.inverse_debt.pk
        assert options[0].max_amount_cents == 3000

    def test_suggestion_limit_accounts_for_confirmed_and_pending_payments(self):
        current_payment = record_payment(
            debt_id=self.debt.pk,
            actor=self.debtor,
            amount_cents=2000,
        )
        confirm_payment(payment_id=current_payment.pk, actor=self.creditor)
        record_payment(debt_id=self.debt.pk, actor=self.debtor, amount_cents=1000)
        record_payment(
            debt_id=self.inverse_debt.pk,
            actor=self.creditor,
            amount_cents=1000,
        )

        options = suggest_compensations(debt_id=self.debt.pk, actor=self.debtor)

        assert len(options) == 1
        assert options[0].current_available_cents == 2000
        assert options[0].reciprocal_available_cents == 2000
        assert options[0].max_amount_cents == 2000

    def test_full_pending_reservation_hides_reciprocal_suggestion(self):
        record_payment(
            debt_id=self.inverse_debt.pk,
            actor=self.creditor,
            amount_cents=3000,
        )

        assert suggest_compensations(debt_id=self.debt.pk, actor=self.debtor) == []

    def test_suggestion_requires_the_debtor(self):
        with pytest.raises(PermissionDenied):
            suggest_compensations(debt_id=self.debt.pk, actor=self.outsider)

    def test_debt_from_inactive_charge_has_no_suggestions(self):
        assert (
            suggest_compensations(
                debt_id=self.inactive_inverse_debt.pk,
                actor=self.creditor,
            )
            == []
        )


class CompensationApplicationTests(TestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana-aplica-compensacao",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan-aplica-compensacao",
            password=TEST_PASSWORD,
        )
        self.outsider = User.objects.create_user(
            username="bruno-aplica-compensacao",
            password=TEST_PASSWORD,
        )
        self.charge = create_charge(
            creator=self.debtor,
            title="Jantar",
            total_cents=5000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=self.charge)
        self.reciprocal_charge = create_charge(
            creator=self.creditor,
            title="Cinema",
            total_cents=3000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        self.reciprocal_debt = Debt.objects.get(
            participation__charge=self.reciprocal_charge,
        )

    def apply(self, **overrides):
        terms = {
            "debt_id": self.debt.pk,
            "reciprocal_debt_id": self.reciprocal_debt.pk,
            "actor": self.debtor,
            "amount_cents": 2000,
            "request_id": uuid4(),
        }
        terms.update(overrides)
        return apply_compensation(**terms)

    def test_partial_compensation_updates_both_debts_and_locks_charges(self):
        request_id = uuid4()
        compensation = self.apply(request_id=request_id)

        assert compensation.debt_id == self.debt.pk
        assert compensation.reciprocal_debt_id == self.reciprocal_debt.pk
        assert compensation.amount_cents == 2000
        assert compensation.initiated_by_id == self.debtor.pk
        assert compensation.created_at is not None
        assert payment_balance(self.debt).open_cents == 3000
        assert payment_balance(self.reciprocal_debt).open_cents == 1000
        self.charge.refresh_from_db()
        self.reciprocal_charge.refresh_from_db()
        assert self.charge.locked_at is not None
        assert self.reciprocal_charge.locked_at is not None

    def test_repeated_submission_returns_same_event_without_reapplying(self):
        request_id = uuid4()
        first = self.apply(request_id=request_id)
        second = self.apply(request_id=request_id)

        assert first.pk == second.pk
        assert Compensation.objects.count() == 1
        assert payment_balance(self.debt).open_cents == 3000
        assert payment_balance(self.reciprocal_debt).open_cents == 1000

    def test_request_id_cannot_be_reused_for_different_terms(self):
        request_id = uuid4()
        self.apply(request_id=request_id)

        with pytest.raises(ValidationError):
            self.apply(request_id=request_id, amount_cents=1000)

        assert Compensation.objects.count() == 1

    def test_invalid_or_unavailable_amount_is_rejected_without_mutations(self):
        for amount_cents in [0, -1, True, 3001]:
            with self.subTest(amount_cents=amount_cents):
                with pytest.raises(ValidationError):
                    self.apply(amount_cents=amount_cents)

                assert not Compensation.objects.exists()
                self.charge.refresh_from_db()
                self.reciprocal_charge.refresh_from_db()
                assert self.charge.locked_at is None
                assert self.reciprocal_charge.locked_at is None

    def test_only_selected_debtor_can_apply_and_debts_must_be_reciprocal(self):
        with pytest.raises(PermissionDenied):
            self.apply(actor=self.outsider)

        unrelated_charge = create_charge(
            creator=self.outsider,
            title="Ingresso",
            total_cents=1000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        unrelated_debt = Debt.objects.get(participation__charge=unrelated_charge)
        with pytest.raises(ValidationError):
            self.apply(reciprocal_debt_id=unrelated_debt.pk)

        assert not Compensation.objects.exists()

    def test_changed_availability_is_rechecked_before_apply(self):
        record_payment(
            debt_id=self.reciprocal_debt.pk,
            actor=self.creditor,
            amount_cents=2500,
        )

        with pytest.raises(ValidationError):
            self.apply(amount_cents=1000)

        assert not Compensation.objects.exists()
        assert payment_balance(self.reciprocal_debt).available_cents == 500


class CompensationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana-concorrencia",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan-concorrencia",
            password=TEST_PASSWORD,
        )
        charge = create_charge(
            creator=self.debtor,
            title="Ingresso ida",
            total_cents=2000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=charge)
        reciprocal_charge = create_charge(
            creator=self.creditor,
            title="Ingresso volta",
            total_cents=2000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        self.reciprocal_debt = Debt.objects.get(
            participation__charge=reciprocal_charge,
        )

    def test_payment_and_compensation_cannot_reserve_the_same_available_value(self):
        barrier = Barrier(2)

        def register_payment():
            close_old_connections()
            debtor = User.objects.get(pk=self.debtor.pk)
            barrier.wait(timeout=5)
            try:
                return record_payment(
                    debt_id=self.debt.pk,
                    actor=debtor,
                    amount_cents=2000,
                )
            except ValidationError as error:
                return error
            finally:
                connections.close_all()

        def compensate_debts():
            close_old_connections()
            debtor = User.objects.get(pk=self.debtor.pk)
            barrier.wait(timeout=5)
            try:
                return apply_compensation(
                    debt_id=self.debt.pk,
                    reciprocal_debt_id=self.reciprocal_debt.pk,
                    actor=debtor,
                    amount_cents=2000,
                    request_id=uuid4(),
                )
            except ValidationError as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            payment_future = executor.submit(register_payment)
            compensation_future = executor.submit(compensate_debts)
            payment_result = payment_future.result(timeout=20)
            compensation_result = compensation_future.result(timeout=20)

        successful_operations = sum(
            not isinstance(result, ValidationError)
            for result in (payment_result, compensation_result)
        )
        assert successful_operations == 1
        assert Payment.objects.count() + Compensation.objects.count() == 1
        balance = payment_balance(self.debt)
        assert balance.available_cents == 0
        assert balance.open_cents in {0, 2000}


class CompensationViewTests(TestCase):
    def setUp(self):
        self.debtor = User.objects.create_user(
            username="ana-tela-compensacao",
            password=TEST_PASSWORD,
        )
        self.creditor = User.objects.create_user(
            username="ryan-tela-compensacao",
            password=TEST_PASSWORD,
        )
        self.outsider = User.objects.create_user(
            username="bruno-tela-compensacao",
            password=TEST_PASSWORD,
        )
        self.charge = create_charge(
            creator=self.debtor,
            title="Jantar",
            total_cents=5000,
            invitee_ids=[],
            creditor_id=self.creditor.pk,
        )
        self.debt = Debt.objects.get(participation__charge=self.charge)
        self.reciprocal_charge = create_charge(
            creator=self.creditor,
            title="Cinema",
            total_cents=3000,
            invitee_ids=[],
            creditor_id=self.debtor.pk,
        )
        self.reciprocal_debt = Debt.objects.get(
            participation__charge=self.reciprocal_charge,
        )

    @property
    def form_prefix(self):
        return f"compensation-{self.debt.pk}-{self.reciprocal_debt.pk}"

    def form_data(self, *, amount="20,00", intent="apply"):
        return {
            f"{self.form_prefix}-reciprocal_debt_id": str(self.reciprocal_debt.pk),
            f"{self.form_prefix}-request_id": str(uuid4()),
            f"{self.form_prefix}-amount": amount,
            "intent": intent,
        }

    def test_detail_shows_inverse_debt_and_default_preview(self):
        self.client.force_login(self.debtor)

        response = self.client.get(reverse("charges:detail", args=[self.charge.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Dívidas que você pode compensar" in content
        assert "Dívida inversa: Cinema" in content
        assert "Disponível nesta dívida" in content
        assert "30,00" in content
        assert "Restante disponível para Pix nesta dívida" in content

    def test_htmx_preview_and_non_htmx_review_do_not_apply_event(self):
        self.client.force_login(self.debtor)
        preview_url = reverse(
            "charges:compensation_preview",
            args=[self.debt.pk, self.reciprocal_debt.pk],
        )
        get_data = {
            f"{self.form_prefix}-reciprocal_debt_id": str(self.reciprocal_debt.pk),
            f"{self.form_prefix}-request_id": str(uuid4()),
            f"{self.form_prefix}-amount": "12,50",
        }

        response = self.client.get(
            preview_url,
            get_data,
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert "12,50" in response.content.decode()
        assert "37,50" in response.content.decode()
        assert not Compensation.objects.exists()

        response = self.client.post(
            reverse(
                "charges:compensation_apply",
                args=[self.debt.pk, self.reciprocal_debt.pk],
            ),
            self.form_data(amount="15,00", intent="preview"),
        )

        assert response.status_code == 200
        assert "Prévia atualizada" in response.content.decode()
        assert "15,00" in response.content.decode()
        assert not Compensation.objects.exists()

    def test_conventional_post_applies_and_redirects_to_charge_detail(self):
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse(
                "charges:compensation_apply",
                args=[self.debt.pk, self.reciprocal_debt.pk],
            ),
            self.form_data(),
        )

        assert response.status_code == 302
        assert response["Location"] == reverse("charges:detail", args=[self.charge.pk])
        assert Compensation.objects.count() == 1
        assert payment_balance(self.debt).open_cents == 3000
        assert payment_balance(self.reciprocal_debt).open_cents == 1000

    def test_htmx_post_applies_and_requests_full_detail_refresh(self):
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse(
                "charges:compensation_apply",
                args=[self.debt.pk, self.reciprocal_debt.pk],
            ),
            self.form_data(),
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert response["HX-Redirect"] == reverse(
            "charges:detail",
            args=[self.charge.pk],
        )
        assert Compensation.objects.count() == 1

    def test_third_party_cannot_preview_or_apply(self):
        self.client.force_login(self.outsider)
        preview_url = reverse(
            "charges:compensation_preview",
            args=[self.debt.pk, self.reciprocal_debt.pk],
        )
        apply_url = reverse(
            "charges:compensation_apply",
            args=[self.debt.pk, self.reciprocal_debt.pk],
        )

        assert self.client.get(preview_url).status_code == 404
        assert self.client.post(apply_url, self.form_data()).status_code == 404
        assert not Compensation.objects.exists()

    def test_invalid_amount_renders_actionable_error_without_applying(self):
        self.client.force_login(self.debtor)

        response = self.client.post(
            reverse(
                "charges:compensation_apply",
                args=[self.debt.pk, self.reciprocal_debt.pk],
            ),
            self.form_data(amount="31,00"),
        )

        assert response.status_code == 400
        assert "O valor excede o disponível nas duas dívidas." in (
            response.content.decode()
        )
        assert not Compensation.objects.exists()

    def test_apply_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.debtor)
        apply_url = reverse(
            "charges:compensation_apply",
            args=[self.debt.pk, self.reciprocal_debt.pk],
        )

        response = csrf_client.post(apply_url, self.form_data())

        assert response.status_code == 403
        assert not Compensation.objects.exists()
