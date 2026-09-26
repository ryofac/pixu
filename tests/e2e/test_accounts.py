import re

import pytest
from allauth.account.models import EmailAddress
from django.urls import reverse
from playwright.sync_api import expect

from .factories import create_user
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("viewport", [(390, 844), (1440, 900)])
def test_profile_email_management_and_active_navigation(page, live_server, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    user = create_user(username="perfil-e2e", name="Pessoa Pixu")
    login_as(page, live_server, user)

    page.goto(app_url(live_server, reverse("accounts:update")))
    page.get_by_label("Nome de exibição").fill("Pessoa Atualizada")
    page.get_by_label("Chave Pix principal").fill("pessoa.atualizada@example.test")
    page.get_by_role("button", name="Salvar alterações", exact=True).click()
    expect(page.get_by_role("heading", name="Meu perfil")).to_be_visible()
    expect(page.locator("main").get_by_role("heading", name="Pessoa Atualizada", exact=True)).to_be_visible()
    expect(page.get_by_text("pessoa.atualizada@example.test", exact=True)).to_be_visible()

    page.goto(app_url(live_server, reverse("account_email")))
    expect(page.get_by_role("heading", name="Endereços de e-mail")).to_be_visible()
    expect(page.get_by_role("radio", name=re.compile(re.escape(user.email)))).to_be_visible()
    page.get_by_label("Novo endereço de e-mail").fill("secundario@example.test")
    page.get_by_role("button", name="Adicionar e-mail", exact=True).click()
    expect(page.get_by_role("radio", name=re.compile("secundario@example\\.test"))).to_be_visible()
    assert EmailAddress.objects.filter(user=user, email="secundario@example.test").exists()

    if viewport[0] < 1024:
        active_navigation_link = page.locator(
            'nav[aria-label="Navegação principal"] a[aria-current="page"]',
        )
        expect(active_navigation_link).to_be_visible()
        expect(active_navigation_link).to_contain_text("Perfil")
    else:
        active_profile_link = page.locator('aside > a[aria-current="page"]')
        expect(active_profile_link).to_be_visible()
        expect(active_profile_link).to_contain_text("Meu perfil")
    body_copy = page.locator("body").inner_text()
    for default_english_copy in ("Make Primary", "Resend Verification", "Add Email Address"):
        assert default_english_copy not in body_copy

    assert_no_horizontal_overflow(page)
    last_action = page.get_by_role("button", name="Adicionar e-mail", exact=True)
    assert_content_reachable_above_mobile_nav(page, last_action)
