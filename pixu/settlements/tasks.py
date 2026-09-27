"""Retryable asynchronous cleanup for private payment receipts."""

from celery import shared_task
from django.core.files.storage import storages

from .models import PendingReceiptDeletion


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 10},
)
def delete_pending_receipt(self, pending_id: int) -> bool:
    """Delete one queued storage object; repeat safely after transient errors."""
    del self
    try:
        pending = PendingReceiptDeletion.objects.get(pk=pending_id)
    except PendingReceiptDeletion.DoesNotExist:
        return False

    storages[pending.storage_alias].delete(pending.file_name)
    pending.delete()
    return True
