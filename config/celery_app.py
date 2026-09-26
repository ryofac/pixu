"""Celery application configuration for Pixu."""

import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("pixu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@setup_logging.connect
def configure_celery_logging(*args, **kwargs):
    """Use Django's logging configuration for worker processes."""

    dictConfig(settings.LOGGING)
