"""Django email backend that queues delivery in Celery."""

from django.core.mail.backends.base import BaseEmailBackend
from django.db import transaction

from .tasks import send_email


class UnsupportedEmailAttachmentsError(ValueError):
    """Raised when a queued message contains attachments."""


class CeleryEmailBackend(BaseEmailBackend):
    """Enqueue Django email messages after the surrounding transaction commits."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        queued = 0
        for message in email_messages:
            if not self._message_is_valid(message):
                continue

            payload = self._serialize_message(message)
            transaction.on_commit(lambda payload=payload: self._enqueue(payload))
            queued += 1
        return queued

    def _message_is_valid(self, message):
        if not message.recipients():
            return False
        if message.attachments:
            if self.fail_silently:
                return False
            raise UnsupportedEmailAttachmentsError
        return True

    def _enqueue(self, payload):
        try:
            send_email.delay(payload)
        except Exception:
            if not self.fail_silently:
                raise

    @staticmethod
    def _serialize_message(message):
        alternatives = [
            (alternative.content, alternative.mimetype)
            for alternative in getattr(message, "alternatives", [])
        ]
        return {
            "subject": message.subject,
            "body": message.body,
            "from_email": message.from_email,
            "to": list(message.to),
            "cc": list(message.cc),
            "bcc": list(message.bcc),
            "reply_to": list(message.reply_to),
            "headers": dict(message.extra_headers),
            "alternatives": alternatives,
        }
