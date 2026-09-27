import pytest
from django.urls import reverse
from playwright.sync_api import expect

from .helpers import app_url
from .helpers import assert_no_horizontal_overflow

pytestmark = pytest.mark.e2e

VIEWPORTS = [(390, 844), (1440, 900)]
THEMES = ["light", "dark"]


@pytest.mark.parametrize("viewport", VIEWPORTS)
@pytest.mark.parametrize("theme", THEMES)
def test_public_landing_sections_scroll_naturally_without_overflow(
    page,
    live_server,
    viewport,
    theme,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(app_url(live_server, reverse("home")))
    page.get_by_label("Aparência").select_option(theme)
    expect(page.locator("html")).to_have_attribute("data-theme", theme)

    sections = page.locator("[data-landing-section]")
    expect(sections).to_have_count(3)
    assert page.evaluate(
        "Array.from(document.querySelectorAll('[data-landing-section]'), "
        "element => element.getAttribute('data-landing-section'))",
    ) == ["rateio", "pagamentos", "historico"]
    assert (
        page.locator("html").evaluate(
            "element => getComputedStyle(element).scrollSnapType",
        )
        == "none"
    )
    assert (
        page.locator("body").evaluate(
            "element => getComputedStyle(element).overflowY",
        )
        != "hidden"
    )
    assert_no_horizontal_overflow(page)

    for index, heading in enumerate(
        [
            "Combinar o rateio fica mais simples.",
            "O Pix acontece fora. O acompanhamento fica por aqui.",
            "Tudo que mudou continua fácil de acompanhar.",
        ],
    ):
        section = sections.nth(index)
        section.evaluate(
            "element => element.scrollIntoView({ block: 'start', "
            "behavior: 'instant' })",
        )
        expect(section.get_by_role("heading", name=heading)).to_be_visible()
        expect(section).to_be_visible()
        assert_no_horizontal_overflow(page)

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    expect(
        page.get_by_role("link", name="Criar minha conta", exact=True),
    ).to_be_visible()
    expect(page.get_by_role("link", name="Entrar", exact=True)).to_be_visible()
