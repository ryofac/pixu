import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from .factories import create_user
from .helpers import DESKTOP_BREAKPOINT
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as

pytestmark = pytest.mark.e2e
VIEWPORTS = [(390, 844), (1440, 900)]
SIDEBAR_MIN_WIDTH = 240
DESKTOP_MAIN_MIN_WIDTH = 900
DEFAULT_ENGLISH_COPY = (
    "Sign In",
    "Sign Up",
    "Log In",
    "Log Out",
    "Password",
    "Email address",
    "Forgot your password",
    "Make Primary",
    "Resend Verification",
)


def assert_product_locale_and_copy(page):
    expect(page.locator("html")).to_have_attribute("lang", "pt-br")
    visible_copy = f"{page.locator('body').inner_text()} {page.title()}"
    for untranslated_copy in DEFAULT_ENGLISH_COPY:
        assert untranslated_copy not in visible_copy


def assert_responsive_shell(page, viewport, active_item):
    assert_product_locale_and_copy(page)
    assert_no_horizontal_overflow(page)

    desktop_sidebar = page.locator("body > div > aside")
    desktop_navigation = desktop_sidebar.get_by_role(
        "navigation",
        name="Navegação principal",
    )
    mobile_navigation = page.locator(
        'body > div > nav[aria-label="Navegação principal"]',
    )

    if viewport[0] < DESKTOP_BREAKPOINT:
        expect(desktop_sidebar).to_be_hidden()
        expect(mobile_navigation).to_be_visible()
        nav_geometry = mobile_navigation.evaluate(
            """element => ({
              position: getComputedStyle(element).position,
              left: element.getBoundingClientRect().left,
              right: element.getBoundingClientRect().right,
              bottom: element.getBoundingClientRect().bottom,
              viewport: innerWidth,
              height: innerHeight,
            })""",
        )
        assert nav_geometry["position"] == "fixed"
        assert nav_geometry["left"] == 0
        assert abs(nav_geometry["right"] - nav_geometry["viewport"]) <= 1
        assert abs(nav_geometry["bottom"] - nav_geometry["height"]) <= 1
        active_link = mobile_navigation.locator('a[aria-current="page"]')
    else:
        expect(desktop_sidebar).to_be_visible()
        expect(desktop_navigation).to_be_visible()
        expect(mobile_navigation).to_be_hidden()
        sidebar_geometry = desktop_sidebar.evaluate(
            """element => ({
              position: getComputedStyle(element).position,
              left: element.getBoundingClientRect().left,
              width: element.getBoundingClientRect().width,
            })""",
        )
        assert sidebar_geometry["position"] == "fixed"
        assert sidebar_geometry["left"] == 0
        assert sidebar_geometry["width"] >= SIDEBAR_MIN_WIDTH
        main_width = page.locator("main").evaluate(
            "element => element.getBoundingClientRect().width",
        )
        assert main_width >= DESKTOP_MAIN_MIN_WIDTH, (
            f"A área principal parece presa a uma moldura mobile: {main_width}px"
        )
        if active_item == "Perfil":
            active_link = desktop_sidebar.locator(':scope > a[aria-current="page"]')
        else:
            active_link = desktop_navigation.locator('a[aria-current="page"]')

    expect(active_link).to_be_visible()
    expected_label = (
        "Meu perfil"
        if active_item == "Perfil" and viewport[0] >= DESKTOP_BREAKPOINT
        else active_item
    )
    expect(active_link).to_contain_text(expected_label)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_public_entry_copy_layout_and_account_navigation(page, live_server, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(app_url(live_server, reverse("home")))

    main = page.locator("main")
    hero = main.get_by_role("region", name="Combinar o rateio fica mais simples.")
    expect(
        hero.get_by_role("heading", name="Combinar o rateio fica mais simples."),
    ).to_be_visible()
    expect(
        hero.get_by_text("Despesas em grupo, com clareza", exact=True),
    ).to_be_visible()
    expect(page.get_by_role("link", name="Entrar", exact=True)).to_have_attribute(
        "href",
        reverse("account_login"),
    )
    assert_product_locale_and_copy(page)
    assert_no_horizontal_overflow(page)
    assert page.locator("body > div > aside").count() == 0
    assert (
        page.locator('body > div > nav[aria-label="Navegação principal"]').count() == 0
    )

    introduction, benefits = hero.locator(":scope > div").all()
    introduction_box = introduction.bounding_box()
    benefits_box = benefits.bounding_box()
    assert introduction_box is not None
    assert benefits_box is not None
    if viewport[0] < DESKTOP_BREAKPOINT:
        assert introduction_box["y"] + introduction_box["height"] <= benefits_box["y"]
    else:
        assert introduction_box["x"] + introduction_box["width"] <= benefits_box["x"]
        main_width = page.locator("main").evaluate(
            "element => element.getBoundingClientRect().width",
        )
        assert main_width >= DESKTOP_MAIN_MIN_WIDTH

    page.get_by_role("link", name="Criar minha conta", exact=True).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_signup")))
    expect(page.get_by_role("heading", name="Crie sua conta")).to_be_visible()
    expect(page.get_by_label("E-mail")).to_be_visible()
    assert_product_locale_and_copy(page)

    page.locator("main").get_by_role("link", name="Entrar", exact=True).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_login")))
    expect(page.get_by_role("heading", name="Entre na sua conta")).to_be_visible()
    expect(page.get_by_label("Nome de usuário")).to_be_visible()
    expect(page.get_by_label("Senha")).to_be_visible()

    page.get_by_role("navigation", name="Ajuda de acesso").get_by_role(
        "link",
        name="Esqueci minha senha",
    ).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_reset_password")))
    expect(page.get_by_role("heading", name="Recuperar senha")).to_be_visible()
    expect(page.get_by_label("E-mail da conta")).to_be_visible()
    expect(page.get_by_role("link", name="Voltar para entrar")).to_be_visible()
    assert_product_locale_and_copy(page)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_authenticated_navigation_and_content_follow_design_breakpoints(
    page, live_server, viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    user = create_user(
        username="navegacao-design-e2e",
        name="Pessoa Pixu",
        pix_key="pessoa@example.test",
    )
    login_as(page, live_server, user)

    expect(page.get_by_role("heading", name="Cobranças", exact=True)).to_be_visible()
    expect(
        page.get_by_role("heading", name="Nenhuma cobrança por aqui"),
    ).to_be_visible()
    expect(page.get_by_role("link", name="Criar cobrança", exact=True)).to_be_visible()
    assert_responsive_shell(page, viewport, "Cobranças")
    assert_content_reachable_above_mobile_nav(
        page,
        page.get_by_role("link", name="Criar cobrança", exact=True),
    )

    if viewport[0] < DESKTOP_BREAKPOINT:
        mobile_navigation = page.locator(
            'body > div > nav[aria-label="Navegação principal"]',
        )
        mobile_navigation.get_by_role("link", name="Convites", exact=True).click()
    else:
        desktop_navigation = page.locator("body > div > aside").get_by_role(
            "navigation",
            name="Navegação principal",
        )
        desktop_navigation.get_by_role("link", name="Convites", exact=True).click()
    expect(page).to_have_url(app_url(live_server, reverse("charges:invites")))
    expect(page.get_by_role("heading", name="Convites", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name="Nenhum convite pendente")).to_be_visible()
    assert_responsive_shell(page, viewport, "Convites")

    if viewport[0] < DESKTOP_BREAKPOINT:
        page.locator('body > div > nav[aria-label="Navegação principal"]').get_by_role(
            "link",
            name="Perfil",
            exact=True,
        ).click()
    else:
        page.locator("body > div > aside").get_by_role(
            "link",
            name=re.compile("Meu perfil"),
        ).click()
    expect(page).to_have_url(
        app_url(live_server, reverse("accounts:detail", args=[user.username])),
    )
    expect(page.get_by_role("heading", name="Meu perfil", exact=True)).to_be_visible()
    expect(
        page.get_by_text(
            "A chave é informada por você. O Pixu não verifica a chave junto ao banco.",
        ),
    ).to_be_visible()
    assert_responsive_shell(page, viewport, "Perfil")
    assert_content_reachable_above_mobile_nav(
        page,
        page.get_by_role("link", name="Gerenciar e-mail", exact=True),
    )

    page.get_by_role("link", name="Gerenciar e-mail", exact=True).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_email")))
    expect(page.get_by_role("heading", name="Endereços de e-mail")).to_be_visible()
    assert_responsive_shell(page, viewport, "Perfil")
    expect(
        page.locator("main").get_by_role("link", name=re.compile("Meu perfil")),
    ).to_be_visible()
