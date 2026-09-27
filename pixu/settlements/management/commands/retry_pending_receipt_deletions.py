from django.core.management.base import BaseCommand

from pixu.settlements.models import PendingReceiptDeletion
from pixu.settlements.tasks import delete_pending_receipt


class Command(BaseCommand):
    help = (
        "Re-enqueue private receipt deletions left pending after a transient failure."
    )

    def handle(self, *args, **options):
        queued = 0
        for pending_id in PendingReceiptDeletion.objects.values_list("pk", flat=True):
            delete_pending_receipt.delay(pending_id)
            queued += 1
        self.stdout.write(self.style.SUCCESS(f"Enfileiradas {queued} remoções."))
