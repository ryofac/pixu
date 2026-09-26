from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from pixu.accounts.models import PixProfile
from pixu.charges.models import Debt
from pixu.charges.services import create_charge
from pixu.settlements.services import record_payment

TEST_PASSWORD = "Pixu-E2E-only!2026"
User = get_user_model()


def create_user(*, username, email=None, name="", password=TEST_PASSWORD, pix_key=""):
    email = email or f"{username}@example.test"
    user = User.objects.create_user(
        username=username,
        email=email,
        name=name,
        password=password,
    )
    EmailAddress.objects.create(
        user=user,
        email=email,
        primary=True,
        verified=True,
    )
    if pix_key:
        PixProfile.objects.create(user=user, pix_key=pix_key)
    return user


def create_active_debt(*, debtor, creditor, amount_cents=10_000, title="Conta compartilhada"):
    charge = create_charge(
        creator=debtor,
        title=title,
        total_cents=amount_cents,
        invitee_ids=[],
        creditor_id=creditor.pk,
        include_creator=True,
    )
    return charge, Debt.objects.get(participation__charge=charge)


def receipt_file(name="comprovante.pdf", content_type="application/pdf"):
    signatures = {
        "application/pdf": b"%PDF-1.7\nPixu test receipt\n%%EOF\n",
        "image/jpeg": b"\xff\xd8\xff\xd9",
        "image/png": b"\x89PNG\r\n\x1a\nsynthetic image data",
    }
    return SimpleUploadedFile(name, signatures[content_type], content_type=content_type)


def create_pending_payment(*, debt, payer, amount_cents=2_000, with_receipt=False):
    return record_payment(
        debt_id=debt.pk,
        actor=payer,
        amount_cents=amount_cents,
        reference="Pagamento de teste E2E",
        receipt=receipt_file() if with_receipt else None,
    )
