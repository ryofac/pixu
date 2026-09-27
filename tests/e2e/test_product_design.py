import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from .factories import create_active_debt
from .factories import create_pending_payment
from .factories import create_user
from .helpers import DESKTOP_BREAKPOINT
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as
from .helpers import wait_for_htmx_response

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
    page.emulate_media(color_scheme="light")
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
    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

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
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    assert_product_locale_and_copy(page)

    page.locator("main").get_by_role("link", name="Entrar", exact=True).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_login")))
    expect(page.get_by_role("heading", name="Entre na sua conta")).to_be_visible()
    expect(page.get_by_label("Nome de usuário")).to_be_visible()
    expect(page.get_by_label("Senha")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    page.get_by_role("navigation", name="Ajuda de acesso").get_by_role(
        "link",
        name="Esqueci minha senha",
    ).click()
    expect(page).to_have_url(app_url(live_server, reverse("account_reset_password")))
    expect(page.get_by_role("heading", name="Recuperar senha")).to_be_visible()
    expect(page.get_by_label("E-mail da conta")).to_be_visible()
    expect(page.get_by_role("link", name="Voltar para entrar")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
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

    expect(page.get_by_role("heading", name="Olá, Pessoa Pixu")).to_be_visible()
    expect(
        page.get_by_text("Você ainda não criou cobranças."),
    ).to_be_visible()
    expect(
        page.locator("main").get_by_role("link", name="Nova cobrança", exact=True),
    ).to_be_visible()
    assert_responsive_shell(page, viewport, "Início")
    assert_content_reachable_above_mobile_nav(
        page,
        page.locator("main").get_by_role("link", name="Nova cobrança", exact=True),
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


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_theme_selector_persists_and_preserves_form_state_through_htmx(
    page,
    live_server,
    viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    user = create_user(username=f"theme-form-{viewport[0]}", name="Tema Pixu")
    login_as(page, live_server, user)

    selector = page.get_by_label("Aparência")
    expect(selector).to_have_value("system")
    expect(page.get_by_role("img", name="Pixu").first).to_be_visible()
    selector.focus()
    page.keyboard.press("ArrowDown")
    focus_outline = selector.evaluate(
        "element => getComputedStyle(element).outlineStyle",
    )
    assert focus_outline == "solid"
    selector.select_option("system")

    page.emulate_media(color_scheme="dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    dark_styles = page.locator("main h1").evaluate(
        "element => ({text: getComputedStyle(element).color, canvas: getComputedStyle(document.body).backgroundColor})",
    )
    assert dark_styles == {"text": "rgb(248, 250, 252)", "canvas": "rgb(15, 23, 42)"}

    page.goto(app_url(live_server, reverse("charges:create")))
    selector = page.get_by_label("Aparência")
    selector.select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme-preference", "dark")
    expect(selector).to_have_value("dark")
    expect(page.locator("body")).to_have_css("background-color", "rgb(15, 23, 42)")

    title = page.get_by_label("Título")
    total = page.get_by_label("Valor total em reais")
    title.fill("Jantar com tema escuro")
    total.fill("35,50")
    selector.select_option("light")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(title).to_have_value("Jantar com tema escuro")
    expect(total).to_have_value("35,50")
    expect(page.locator("body")).to_have_css("background-color", "rgb(255, 244, 243)")

    wait_for_htmx_response(
        page,
        reverse("charges:preview"),
        lambda: page.get_by_role(
            "button",
            name="Conferir cotas · dividir igualmente",
        ).click(),
    )
    expect(page.locator("#share-preview")).to_contain_text("Prévia do rateio")
    expect(title).to_have_value("Jantar com tema escuro")
    expect(total).to_have_value("35,50")
    expect(page.locator("html")).to_have_attribute("data-theme-preference", "light")
    assert_no_horizontal_overflow(page)

    counterparty = create_user(username=f"theme-counterparty-{viewport[0]}")
    charge, debt = create_active_debt(
        debtor=user,
        creditor=counterparty,
        title=f"Cobrança em dois temas {viewport[0]}",
    )
    reverse_charge, reverse_debt = create_active_debt(
        debtor=counterparty,
        creditor=user,
        title=f"Cobrança inversa em dois temas {viewport[0]}",
    )
    create_pending_payment(debt=debt, payer=user)

    pages = [
        (reverse("charges:list"), "Cobranças"),
        (reverse("charges:invites"), "Convites"),
        (reverse("accounts:detail", args=[user.username]), "Meu perfil"),
        (reverse("charges:detail", args=[charge.pk]), charge.title),
        (reverse("charges:detail", args=[reverse_charge.pk]), reverse_charge.title),
        (reverse("settlements:record", args=[debt.pk]), "Registrar pagamento"),
    ]
    for theme in ("light", "dark"):
        page.get_by_label("Aparência").select_option(theme)
        for path, visible_text in pages:
            page.goto(app_url(live_server, path))
            expect(page.locator("html")).to_have_attribute("data-theme", theme)
            expect(page.locator("body")).to_have_css(
                "background-color",
                "rgb(255, 244, 243)" if theme == "light" else "rgb(15, 23, 42)",
            )
            expect(page.locator("main")).to_contain_text(visible_text)

            if path == reverse("charges:detail", args=[charge.pk]):
                debt_card = page.locator(f"#debt-{debt.pk}")
                expect(debt_card).to_contain_text("Pendente")
                expect(debt_card).to_contain_text("Dívidas que você pode compensar")
                if theme == "dark":
                    reciprocal_option = page.locator(
                        "article[aria-labelledby="
                        f"'compensation-option-{debt.pk}-{reverse_debt.pk}']",
                    )
                    wait_for_htmx_response(
                        page,
                        reverse(
                            "charges:compensation_apply",
                            args=[debt.pk, reverse_debt.pk],
                        ),
                        lambda: reciprocal_option.get_by_role(
                            "button", name="Revisar valor",
                        ).click(),
                    )
                    compensation_status = page.locator(
                        "#charge-content > [data-focus-after-swap]",
                    )
                    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                    expect(compensation_status).to_contain_text(
                        "Prévia atualizada; nenhuma compensação foi aplicada.",
                    )
                    expect(compensation_status).to_have_css(
                        "background-color",
                        "rgb(18, 53, 38)",
                    )
                    expect(compensation_status).to_have_css(
                        "color",
                        "rgb(134, 239, 172)",
                    )
                    expect(compensation_status).to_be_focused()


def test_system_theme_tracks_device_and_explicit_choice_wins(page, live_server):
    page.emulate_media(color_scheme="dark")
    page.goto(app_url(live_server, reverse("home")))
    selector = page.get_by_label("Aparência")
    expect(selector).to_have_value("system")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    page.emulate_media(color_scheme="light")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    selector.select_option("dark")
    page.emulate_media(color_scheme="light")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    selector.select_option("system")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")


def test_theme_choice_falls_back_to_session_storage_when_local_storage_is_blocked(
    page,
    live_server,
):
    page.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() {throw new Error('blocked')}})",
    )
    page.emulate_media(color_scheme="dark")
    page.goto(app_url(live_server, reverse("home")))
    selector = page.get_by_label("Aparência")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    selector.select_option("light")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    page.goto(app_url(live_server, reverse("account_login")))
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(page.get_by_label("Aparência")).to_have_value("light")


def test_theme_remains_usable_when_all_browser_storage_is_blocked(page, live_server):
    page.add_init_script(
        """
        for (const key of ['localStorage', 'sessionStorage']) {
          Object.defineProperty(window, key, {get() {throw new Error('blocked')}});
        }
        """,
    )
    page.goto(app_url(live_server, reverse("home")))
    selector = page.get_by_label("Aparência")
    selector.select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(page.locator("body")).to_have_css("background-color", "rgb(15, 23, 42)")
