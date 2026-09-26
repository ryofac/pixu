import pytest

# ruff: noqa: PLR2004, S105
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from pixu.accounts.models import PixProfile
from pixu.accounts.models import User
from pixu.charges.models import Debt
from pixu.charges.services import create_charge
from pixu.charges.services import edit_participation_shares

from .models import Payment
from .services import confirm_payment
from .services import delete_receipt
from .services import payment_balance
from .services import record_payment
from .services import reject_payment
from .services import replace_receipt

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
            pending_cents=2000,
            open_cents=10000,
            available_cents=8000,
        )
        self.charge.refresh_from_db()
        assert self.charge.locked_at is not None

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
        assert payment_balance(self.debt).open_cents == 8000

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
        assert b"".join(response.streaming_content).startswith(b"%PDF")

        outsider_client = Client()
        outsider_client.force_login(self.outsider)
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
        assert 'accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"' in content

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
        assert "Pagamento confirmado." in response.content.decode()
        assert "30,00" in response.content.decode()

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
