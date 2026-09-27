# ruff: noqa: PLR2004, S105

from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from pixu.charges.models import Debt
from pixu.charges.services import absolutely_delete_charge
from pixu.charges.services import accept_participation
from pixu.charges.services import create_charge

from .models import PendingReceiptDeletion
from .services import record_payment
from .tasks import delete_pending_receipt

pytestmark = [
    pytest.mark.skipif(
        not settings.PIXU_S3_ENDPOINT_URL,
        reason="O storage S3-like local não está configurado neste ambiente.",
    ),
]

User = get_user_model()
TEST_PASSWORD = "Pixu-tests-only!2026"


class S3LikeReceiptIntegrationTests(TestCase):
    def test_receipt_upload_inline_read_and_absolute_cleanup(self):
        storage_options = {
            "bucket_name": settings.PIXU_S3_BUCKET_NAME,
            "endpoint_url": settings.PIXU_S3_ENDPOINT_URL,
            "region_name": settings.PIXU_S3_REGION_NAME,
            "access_key": settings.PIXU_S3_ACCESS_KEY_ID,
            "secret_key": settings.PIXU_S3_SECRET_ACCESS_KEY,
            "addressing_style": settings.PIXU_S3_ADDRESSING_STYLE,
            "use_ssl": settings.PIXU_S3_USE_SSL,
            "querystring_auth": True,
            "file_overwrite": False,
            "default_acl": None,
        }
        storage_settings = {
            **settings.STORAGES,
            "default": {
                "BACKEND": "storages.backends.s3.S3Storage",
                "OPTIONS": storage_options,
            },
        }

        with self.settings(STORAGES=storage_settings):
            storage = storages["default"]
            receipt_name = ""
            try:
                creator = User.objects.create_user(username="charge-creator")
                payer = User.objects.create_user(username="payer")
                receiver = User.objects.create_user(username="receiver")
                administrator = User.objects.create_superuser(
                    username="storage-admin",
                    email="storage-admin@example.test",
                    password=TEST_PASSWORD,
                )
                charge = create_charge(
                    creator=creator,
                    title="Rateio de validação do storage",
                    total_cents=10000,
                    invitee_ids=[payer.pk],
                    creditor_id=receiver.pk,
                    include_creator=False,
                    shares_by_user={payer.pk: 10000},
                )
                participation = charge.participations.get(user=payer)
                accept_participation(
                    participation_id=participation.pk,
                    actor=payer,
                )
                debt = Debt.objects.get(participation=participation)
                payment = record_payment(
                    debt_id=debt.pk,
                    actor=payer,
                    amount_cents=10000,
                    receipt=SimpleUploadedFile(
                        "comprovante-s3.pdf",
                        b"%PDF-1.7\ncomprovante do garage",
                        content_type="application/pdf",
                    ),
                )
                receipt_name = payment.receipt.name
                assert storage.exists(receipt_name)

                creator_client = Client()
                creator_client.force_login(creator)
                receipt_response = creator_client.get(
                    reverse("settlements:receipt", args=[payment.pk]),
                )
                assert receipt_response.status_code == 200
                assert receipt_response["Content-Disposition"].startswith("inline;")
                assert b"".join(receipt_response.streaming_content).startswith(b"%PDF")

                with (
                    patch("pixu.settlements.tasks.delete_pending_receipt.delay"),
                    self.captureOnCommitCallbacks(execute=True),
                ):
                    absolutely_delete_charge(
                        charge_id=charge.pk,
                        actor=administrator,
                    )

                pending = PendingReceiptDeletion.objects.get(file_name=receipt_name)
                assert pending.storage_alias == "default"
                assert storage.exists(receipt_name)
                assert delete_pending_receipt.run(pending.pk)
                assert not storage.exists(receipt_name)
                assert not PendingReceiptDeletion.objects.filter(pk=pending.pk).exists()
            finally:
                if receipt_name:
                    storage.delete(receipt_name)
