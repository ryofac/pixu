from allauth.account.forms import AddEmailForm
from allauth.account.forms import ChangePasswordForm
from allauth.account.forms import LoginForm
from allauth.account.forms import ResetPasswordForm
from allauth.account.forms import ResetPasswordKeyForm
from allauth.account.forms import SetPasswordForm
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={
                "email": _("E-mail"),
                "username": _("Nome de usuário"),
                "password1": _("Senha"),
                "password2": _("Confirme a senha"),
            },
            placeholders={
                "email": _("voce@exemplo.com"),
                "username": _("Como você quer ser identificado?"),
            },
        )


class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={
                "login": _("Nome de usuário"),
                "password": _("Senha"),
                "remember": _("Continuar conectado"),
            },
            placeholders={"login": _("Nome de usuário")},
        )
        if "password" in self.fields:
            self.fields["password"].help_text = ""


class UserResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={"email": _("E-mail da conta")},
            placeholders={"email": _("voce@exemplo.com")},
        )


class UserChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={
                "oldpassword": _("Senha atual"),
                "password1": _("Nova senha"),
                "password2": _("Confirme a nova senha"),
            },
        )


class UserSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={
                "password1": _("Nova senha"),
                "password2": _("Confirme a nova senha"),
            },
        )


class UserResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={
                "password1": _("Nova senha"),
                "password2": _("Confirme a nova senha"),
            },
        )


class UserAddEmailForm(AddEmailForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_account_fields(
            self,
            labels={"email": _("Novo endereço de e-mail")},
            placeholders={"email": _("voce@exemplo.com")},
        )


def _localize_account_fields(form, *, labels, placeholders=None):
    placeholders = placeholders or {}
    for name, label in labels.items():
        field = form.fields.get(name)
        if field is None:
            continue
        field.label = label
        field.error_messages["required"] = _("Este campo é obrigatório.")
        field.error_messages["invalid"] = _("Informe um valor válido.")
        if name in placeholders:
            field.widget.attrs["placeholder"] = placeholders[name]


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
