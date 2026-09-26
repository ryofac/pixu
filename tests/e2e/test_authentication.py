import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from playwright.sync_api import expect

from .factories import TEST_PASSWORD
from .factories import create_user
from .helpers import app_url
from .helpers import login_as

pytestmark = pytest.mark.e2e
User = get_user_model()


def test_signup_creates_account_and_shows_localized_confirmation(page, live_server):
    username = "cadastro-e2e"
    page.goto(app_url(live_server, reverse("account_signup")))
    page.get_by_label("E-mail").fill(f"{username}@example.test")
    page.get_by_label("Nome de usuário").fill(username)
    page.get_by_label("Senha", exact=True).fill(TEST_PASSWORD)
    page.get_by_label("Confirme a senha").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Criar conta", exact=True).click()

    expect(page.get_by_role("heading", name="Confira seu e-mail")).to_be_visible()
    expect(page.get_by_text("Enviamos uma mensagem para confirmar", exact=False)).to_be_visible()
    user = User.objects.get(username=username)
    assert not EmailAddress.objects.get(user=user).verified
    assert len(mail.outbox) == 1


def test_login_and_logout_work_through_allauth_pages(page, live_server):
    user = create_user(username="login-e2e")
    login_as(page, live_server, user)

    page.goto(app_url(live_server, reverse("account_logout")))
    expect(page.get_by_role("heading", name="Sair da conta")).to_be_visible()
    page.get_by_role("button", name="Sair", exact=True).click()
    expect(page.get_by_text("Você saiu.", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Entrar", exact=True)).to_have_attribute("href", reverse("account_login"))


def test_password_reset_request_uses_localized_copy_and_memory_email(page, live_server):
    user = create_user(username="recuperar-e2e")
    mail.outbox.clear()
    page.goto(app_url(live_server, reverse("account_reset_password")))
    page.get_by_label("E-mail da conta").fill(user.email)
    page.get_by_role("button", name="Enviar instruções", exact=True).click()

    expect(page.get_by_role("heading", name="Confira seu e-mail")).to_be_visible()
    expect(page.get_by_text("Se houver uma conta associada", exact=False)).to_be_visible()
    assert len(mail.outbox) == 1
