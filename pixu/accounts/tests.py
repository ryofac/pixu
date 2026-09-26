# ruff: noqa: PLR2004, S105

import re
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from urllib.parse import urlsplit

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import send_mail
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from pixu.accounts.models import PixProfile
from pixu.accounts.tasks import send_email

User = get_user_model()
TEST_PASSWORD = "Pixu-tests-only!2026"


class AccountFlowTests(TestCase):
    def create_user(
        self,
        *,
        username="ana",
        email="ana@example.test",
        password=TEST_PASSWORD,
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=True,
        )
        return user

    @staticmethod
    def email_path(message):
        match = re.search(r"https?://[^\s<>]+", message.body)
        if not match:
            message = "O e-mail não contém um link de ação."
            raise AssertionError(message)
        return urlsplit(match.group(0).rstrip(".,;)")).path

    def test_login_screen_uses_pixu_layout_and_links_to_recovery(self):
        response = self.client.get(reverse("account_login"))

        assert response.status_code == 200
        self.assertContains(response, "Entre na sua conta")
        self.assertContains(response, "Despesas compartilhadas, com mais clareza.")
        self.assertContains(response, reverse("account_reset_password"))

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
    def test_signup_rejects_mismatched_passwords_without_creating_account(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "bruno@example.test",
                "username": "bruno",
                "password1": "UmaSenha!Segura2026",
                "password2": "OutraSenha!Segura2026",
            },
        )

        assert response.status_code == 200
        assert not User.objects.filter(username="bruno").exists()
        self.assertContains(response, 'role="alert"', status_code=200)
        self.assertContains(response, 'aria-invalid="true"', status_code=200)

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
    def test_signup_sends_confirmation_email_and_confirm_link_verifies_address(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "bruno@example.test",
                "username": "bruno",
                "password1": "UmaSenha!Segura2026",
                "password2": "UmaSenha!Segura2026",
            },
            follow=True,
        )

        assert response.status_code == 200
        self.assertContains(response, "Confira seu e-mail")
        assert User.objects.filter(username="bruno").count() == 1
        assert len(mail.outbox) == 1
        email_address = EmailAddress.objects.get(user__username="bruno")
        assert not email_address.verified

        confirmation_path = self.email_path(mail.outbox[0])
        assert self.client.get(confirmation_path).status_code == 200
        response = self.client.post(confirmation_path)

        email_address.refresh_from_db()
        assert email_address.verified
        assert response.status_code in (200, 302)

    def test_login_and_logout_use_username_credentials(self):
        user = self.create_user()
        response = self.client.post(
            reverse("account_login"),
            {"login": user.username, "password": TEST_PASSWORD},
        )

        assert response.status_code == 302
        assert int(self.client.session["_auth_user_id"]) == user.pk
        assert self.client.get(reverse("account_logout")).status_code == 200
        response = self.client.post(reverse("account_logout"))
        assert response.status_code == 302
        assert "_auth_user_id" not in self.client.session

    def test_password_reset_email_link_changes_password(self):
        self.create_user()
        response = self.client.post(
            reverse("account_reset_password"),
            {"email": "ana@example.test"},
            follow=True,
        )

        assert response.status_code == 200
        self.assertContains(response, "Se houver uma conta associada")
        assert len(mail.outbox) == 1
        reset_path = self.email_path(mail.outbox[0])
        reset_response = self.client.get(reset_path, follow=True)
        assert reset_response.status_code == 200
        reset_path = reset_response.request["PATH_INFO"]
        response = self.client.post(
            reset_path,
            {
                "password1": "Nova!SenhaSegura2026",
                "password2": "Nova!SenhaSegura2026",
            },
            follow=True,
        )

        assert response.status_code == 200
        self.assertContains(response, "Senha atualizada")
        assert User.objects.get(username="ana").check_password("Nova!SenhaSegura2026")

    def test_profile_update_persists_only_for_authenticated_user(self):
        owner = self.create_user()
        other = self.create_user(
            username="bruno",
            email="bruno@example.test",
        )
        other_profile = PixProfile.objects.create(
            user=other, pix_key="bruno@example.test",
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse("accounts:update"),
            {
                "name": "Ana de Souza",
                "pix_key": "ana@example.test",
                "user_id": other.pk,
            },
        )

        assert response.status_code == 302
        assert User.objects.get(pk=owner.pk).name == "Ana de Souza"
        assert PixProfile.objects.get(user=owner).pix_key == "ana@example.test"
        other_profile.refresh_from_db()
        assert other_profile.pix_key == "bruno@example.test"
        other_response = self.client.get(
            reverse("accounts:detail", args=[other.username]),
        )
        assert other_response.status_code == 200
        self.assertNotContains(other_response, "ana@example.test")

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=True, ACCOUNT_RATE_LIMITS={})
    def test_complete_account_journey_through_forms_with_csrf(self):  # noqa: PLR0915
        self.client = Client(enforce_csrf_checks=True)

        def submit_form(path, data=None):
            page = self.client.get(path, follow=True)
            assert page.status_code == 200
            token = re.search(
                r'name="csrfmiddlewaretoken" value="([^"]+)"',
                page.content.decode(),
            )
            assert token is not None
            return self.client.post(
                page.request["PATH_INFO"],
                {"csrfmiddlewaretoken": token.group(1), **(data or {})},
                follow=True,
            )

        response = submit_form(
            reverse("account_signup"),
            {
                "username": "jornada",
                "email": "jornada@example.test",
                "password1": TEST_PASSWORD,
                "password2": TEST_PASSWORD,
            },
        )
        self.assertContains(response, "Confira seu e-mail")
        user = User.objects.get(username="jornada")
        email_address = EmailAddress.objects.get(user=user)
        assert not email_address.verified
        assert "_auth_user_id" not in self.client.session

        confirmation_path = self.email_path(mail.outbox[-1])
        response = submit_form(confirmation_path)
        assert response.status_code == 200
        email_address.refresh_from_db()
        assert email_address.verified

        response = submit_form(
            reverse("account_login"),
            {"login": user.username, "password": TEST_PASSWORD},
        )
        assert response.request["PATH_INFO"] == reverse("home")
        self.assertContains(response, "Suas cobranças")
        assert int(self.client.session["_auth_user_id"]) == user.pk

        profile = self.client.get(user.get_absolute_url())
        self.assertContains(profile, reverse("accounts:update"))
        response = submit_form(
            reverse("accounts:update"),
            {"name": "Pessoa da jornada", "pix_key": "jornada@example.test"},
        )
        self.assertContains(response, "Pessoa da jornada")
        self.assertContains(response, "jornada@example.test")
        self.assertContains(response, "O Pixu não verifica a chave junto ao banco.")
        assert PixProfile.objects.get(user=user).pix_key == "jornada@example.test"
        self.assertContains(self.client.get(reverse("account_email")), user.email)
        assert self.client.get(reverse("charges:create")).status_code == 200
        assert self.client.get(reverse("charges:invites")).status_code == 200

        submit_form(reverse("account_logout"))
        assert "_auth_user_id" not in self.client.session
        mail.outbox.clear()
        response = submit_form(reverse("account_reset_password"), {"email": user.email})
        self.assertContains(response, "Se houver uma conta associada")
        assert len(mail.outbox) == 1
        original_reset_path = self.email_path(mail.outbox[0])
        reset_page = self.client.get(original_reset_path, follow=True)
        self.assertContains(reset_page, "Criar nova senha")
        new_password = "Nova!SenhaDaJornada2026"
        response = submit_form(
            reset_page.request["PATH_INFO"],
            {"password1": new_password, "password2": new_password},
        )
        self.assertContains(response, "Senha atualizada")

        response = submit_form(
            reverse("account_login"),
            {"login": user.username, "password": TEST_PASSWORD},
        )
        assert "_auth_user_id" not in self.client.session
        self.assertContains(response, 'role="alert"')
        response = submit_form(
            reverse("account_login"),
            {"login": user.username, "password": new_password},
        )
        assert response.request["PATH_INFO"] == reverse("home")
        assert int(self.client.session["_auth_user_id"]) == user.pk

        replay = Client().get(original_reset_path, follow=True)
        self.assertContains(replay, "Link inválido")
        self.assertContains(replay, reverse("account_reset_password"))

    @override_settings(
        ACCOUNT_ALLOW_REGISTRATION=True,
        EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    )
    def test_local_console_backend_outputs_confirmation_and_recovery_links(self):
        output = StringIO()
        with redirect_stdout(output):
            response = self.client.post(
                reverse("account_signup"),
                {
                    "username": "consoleuser",
                    "email": "console@example.test",
                    "password1": TEST_PASSWORD,
                    "password2": TEST_PASSWORD,
                },
            )
        assert response.status_code == 302
        assert "To: console@example.test" in output.getvalue()
        assert "confirm-email" in output.getvalue()
        assert TEST_PASSWORD not in output.getvalue()

        output = StringIO()
        with redirect_stdout(output):
            response = self.client.post(
                reverse("account_reset_password"),
                {"email": "console@example.test"},
            )
        assert response.status_code == 302
        assert "To: console@example.test" in output.getvalue()
        assert "password/reset/key" in output.getvalue()
        assert TEST_PASSWORD not in output.getvalue()

    @override_settings(
        EMAIL_BACKEND="pixu.accounts.email_backends.CeleryEmailBackend",
        CELERY_EMAIL_DELIVERY_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_celery_email_backend_delivers_after_commit(self):
        with (
            patch("pixu.accounts.email_backends.send_email.delay") as enqueue,
            self.captureOnCommitCallbacks(execute=True) as callbacks,
        ):
            sent = send_mail(
                "Mensagem assíncrona",
                "Corpo da mensagem",
                "Pixu <noreply@example.test>",
                ["ana@example.test"],
            )

        assert sent == 1
        assert len(callbacks) == 1
        enqueue.assert_called_once()
        send_email.apply(args=[enqueue.call_args.args[0]])
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Mensagem assíncrona"
