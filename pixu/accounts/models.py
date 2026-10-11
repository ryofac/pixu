from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for Pixu.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    onboarding_completed = models.BooleanField(
        _("onboarding concluído"),
        default=True,
    )
    allow_direct_charge_inclusion = models.BooleanField(
        _("permitir inclusão direta em cobranças"),
        default=False,
    )

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("accounts:detail", kwargs={"username": self.username})


class PixProfile(models.Model):
    """A user's primary Pix key, supplied by the account holder."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="pix_profile",
        verbose_name=_("usuário"),
    )
    pix_key = models.CharField(_("chave Pix principal"), blank=True, max_length=255)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("perfil Pix")
        verbose_name_plural = _("perfis Pix")

    def __str__(self) -> str:
        return f"Perfil Pix de {self.user}"
