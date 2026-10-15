from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExtractsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pixu.extracts"
    verbose_name = _("Extracts")
