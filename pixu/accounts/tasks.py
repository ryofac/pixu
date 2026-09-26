"""Asynchronous account-related tasks."""

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail import get_connection


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_email(self, payload):
    """Deliver one serialized email through the configured SMTP backend."""

    del self
    connection = get_connection(
        backend=settings.CELERY_EMAIL_DELIVERY_BACKEND,
        fail_silently=False,
    )
    email = EmailMultiAlternatives(
        subject=payload["subject"],
        body=payload["body"],
        from_email=payload["from_email"],
        to=payload.get("to") or [],
        cc=payload.get("cc") or [],
        bcc=payload.get("bcc") or [],
        reply_to=payload.get("reply_to") or [],
        headers=payload.get("headers") or {},
        connection=connection,
    )
    for content, mimetype in payload.get("alternatives") or []:
        email.attach_alternative(content, mimetype)
    return email.send()
