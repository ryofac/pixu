from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChargesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pixu.charges"
    verbose_name = _("Charges")
