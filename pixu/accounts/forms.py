from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import PixProfile
from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class PixProfileForm(forms.ModelForm):
    class Meta:
        model = PixProfile
        fields = ["pix_key"]
        help_texts = {
            "pix_key": _(
                "Chave informada por você; o Pixu não a verifica junto ao banco.",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pix_key"].widget.attrs.update(
            {
                "autocomplete": "off",
                "maxlength": "255",
            },
        )


class AccountProfileForm(forms.Form):
    name = forms.CharField(label=_("Nome de exibição"), max_length=255, required=False)
    pix_key = forms.CharField(
        label=_("Chave Pix principal"),
        max_length=255,
        required=False,
        help_text=_(
            "A chave é informada por você. O Pixu não verifica a chave junto ao banco.",
        ),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": _("Telefone, e-mail, CPF/CNPJ ou chave aleatória"),
            },
        ),
    )

    def __init__(self, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["name"].initial = user.name
        self.fields["pix_key"].initial = (
            user.pix_profile.pix_key if hasattr(user, "pix_profile") else ""
        )

    def save(self) -> User:
        with transaction.atomic():
            self.user.name = self.cleaned_data["name"].strip()
            self.user.save(update_fields=["name"])
            PixProfile.objects.update_or_create(
                user=self.user,
                defaults={"pix_key": self.cleaned_data["pix_key"].strip()},
            )
        return self.user
