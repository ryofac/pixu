import re

import pytest
from allauth.account.models import EmailAddress
from django.urls import reverse
from playwright.sync_api import expect

from pixu.charges.models import Charge

from .factories import create_active_debt
from .factories import create_user
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("viewport", [(375, 844), (1024, 900)])
def test_authenticated_user_detail_shows_shared_charge_and_profile_navigation(
    page,
    live_server,
    viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.add_init_script(
        """Object.defineProperty(navigator, 'clipboard', {
          configurable: true,
          value: { writeText: text => {
            document.documentElement.dataset.clipboardText = text;
            return Promise.resolve();
          } }
        });""",
    )
    visitor = create_user(username=f"visitante-{viewport[0]}", name="Pessoa Visitante")
    target = create_user(
        username=f"alvo-{viewport[0]}",
        name="Pessoa Alvo",
        pix_key=f"alvo-{viewport[0]}@example.test",
    )
    common, _debt = create_active_debt(
        debtor=target,
        creditor=visitor,
        title="Despesa em comum",
    )
    Charge.objects.create(
        creator=target,
        creditor=target,
        title="Despesa privada do alvo",
        total_cents=10_000,
        state=Charge.State.ACTIVE,
    )
    login_as(page, live_server, visitor)

    page.goto(app_url(live_server, reverse("accounts:detail", args=[target.username])))
    expect(page.get_by_role("heading", name="Perfil de Pessoa Alvo")).to_be_visible()
    expect(page.get_by_text("Informações declaradas por Pessoa Alvo.", exact=False)).to_have_count(0)
    expect(page.get_by_text("Este perfil é somente leitura.", exact=False)).to_have_count(0)
    back_link = page.get_by_role("link", name="Voltar para cobranças")
    expect(back_link).to_have_class(re.compile("focus-visible:outline-2"))
    expect(page.get_by_text(target.pix_profile.pix_key, exact=True)).to_be_visible()
    copy_key_button = page.get_by_role("button", name="Copiar chave Pix")
    expect(copy_key_button).to_be_visible()
    expect(copy_key_button).to_have_class(re.compile("min-h-11"))
    expect(copy_key_button).to_have_class(re.compile("focus-visible:outline-2"))
    copy_key_button.click()
    expect(page.get_by_role("button", name="Chave copiada!")).to_be_visible()
    assert page.locator("html").get_attribute("data-clipboard-text") == target.pix_profile.pix_key
    shared_link = page.get_by_role("link", name=re.compile("Despesa em comum"))
    expect(shared_link).to_have_attribute(
        "href",
        reverse("charges:detail", args=[common.pk]),
    )
    expect(page.get_by_text("Despesa privada do alvo", exact=True)).to_have_count(0)
    assert_no_horizontal_overflow(page)

    page.locator("html").evaluate("element => element.dataset.theme = 'dark'")
    assert_no_horizontal_overflow(page)
    shared_link.click()
    expect(page.get_by_role("heading", name="Despesa em comum")).to_be_visible()
    profile_link = page.get_by_role("link", name="Pessoa Alvo", exact=True).first
    expect(profile_link).to_have_attribute(
        "href",
        reverse("accounts:detail", args=[target.username]),
    )
    assert_no_horizontal_overflow(page)

    page.goto(app_url(live_server, reverse("accounts:detail", args=[visitor.username])))
    expect(page.get_by_role("heading", name="Meu perfil", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Editar perfil")).to_be_visible()
    expect(page.get_by_role("link", name="Gerenciar e-mail")).to_be_visible()
    expect(page.get_by_role("button", name="Sair da conta")).to_be_visible()
    expect(page.get_by_role("heading", name="Cobranças em comum")).to_have_count(0)
    assert_no_horizontal_overflow(page)
    assert_content_reachable_above_mobile_nav(
        page,
        page.get_by_role("button", name="Sair da conta"),
    )


@pytest.mark.parametrize("viewport", [(390, 844), (1440, 900)])
def test_profile_email_management_and_active_navigation(page, live_server, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    user = create_user(username="perfil-e2e", name="Pessoa Pixu")
    login_as(page, live_server, user)

    page.goto(app_url(live_server, reverse("accounts:update")))
    direct_inclusion = page.get_by_role(
        "checkbox",
        name="Permitir inclusão direta em cobranças",
    )
    expect(direct_inclusion).to_be_visible()
    expect(direct_inclusion).not_to_be_checked()
    direct_inclusion.check()
    page.get_by_label("Nome de exibição").fill("Pessoa Atualizada")
    page.get_by_label("Chave Pix principal").fill("pessoa.atualizada@example.test")
    page.get_by_role("button", name="Salvar alterações", exact=True).click()
    expect(page.get_by_role("heading", name="Meu perfil")).to_be_visible()
    expect(
        page.locator("main").get_by_role(
            "heading",
            name="Pessoa Atualizada",
            exact=True,
        ),
    ).to_be_visible()
    expect(
        page.get_by_text("pessoa.atualizada@example.test", exact=True),
    ).to_be_visible()
    user.refresh_from_db()
    assert user.allow_direct_charge_inclusion

    page.goto(app_url(live_server, reverse("account_email")))
    expect(page.get_by_role("heading", name="Endereços de e-mail")).to_be_visible()
    expect(
        page.get_by_role("radio", name=re.compile(re.escape(user.email))),
    ).to_be_visible()
    page.get_by_label("Novo endereço de e-mail").fill("secundario@example.test")
    page.get_by_role("button", name="Adicionar e-mail", exact=True).click()
    expect(
        page.get_by_role("radio", name=re.compile("secundario@example\\.test")),
    ).to_be_visible()
    assert EmailAddress.objects.filter(
        user=user,
        email="secundario@example.test",
    ).exists()

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
    for default_english_copy in (
        "Make Primary",
        "Resend Verification",
        "Add Email Address",
    ):
        assert default_english_copy not in body_copy

    assert_no_horizontal_overflow(page)
    last_action = page.get_by_role("button", name="Adicionar e-mail", exact=True)
    assert_content_reachable_above_mobile_nav(page, last_action)


def test_onboarding_recommends_direct_inclusion_without_enabling_it(page, live_server):
    user = create_user(username="onboarding-inclusao-e2e", name="Nova conta")
    user.onboarding_completed = False
    user.save(update_fields=["onboarding_completed"])
    page.goto(app_url(live_server, reverse("account_login")))
    page.get_by_label("Nome de usuário").fill(user.username)
    page.get_by_label("Senha").fill("Pixu-E2E-only!2026")
    page.get_by_role("button", name="Entrar", exact=True).click()

    expect(page).to_have_url(re.compile(reverse("accounts:onboarding")))
    expect(page.get_by_role("heading", name="Uma preferência para convites futuros")).to_be_visible()
    expect(page.get_by_text("Recomendamos considerar essa opção", exact=False)).to_be_visible()
    user.refresh_from_db()
    assert not user.allow_direct_charge_inclusion
