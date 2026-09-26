from urllib.parse import urljoin

from django.urls import reverse
from playwright.sync_api import expect

from .factories import TEST_PASSWORD

DESKTOP_BREAKPOINT = 1024


def app_url(live_server, path):
    return urljoin(live_server.url, path)


def login_as(page, live_server, user, password=TEST_PASSWORD):
    page.context.clear_cookies()
    page.goto(app_url(live_server, reverse("account_login")))
    page.get_by_label("Nome de usuário").fill(user.username)
    page.get_by_label("Senha").fill(password)
    page.get_by_role("button", name="Entrar", exact=True).click()
    page.wait_for_url(app_url(live_server, reverse("home")))


def wait_for_htmx_response(page, path_fragment, action):
    with page.expect_response(
        lambda response: (
            path_fragment in response.url and response.request.method == "POST"
        ),
    ):
        action()


def capture_page_state(page):
    return page.evaluate(
        """() => ({
          url: location.href,
          title: document.title,
          viewport: { width: innerWidth, height: innerHeight },
          document: {
            clientWidth: document.documentElement.clientWidth,
            scrollWidth: document.documentElement.scrollWidth,
          },
          mainText: document.querySelector('main')?.innerText?.slice(0, 500) || '',
        })""",
    )


def assert_no_horizontal_overflow(page):
    measurements = page.evaluate(
        """() => ({
          viewport: innerWidth,
          document: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
        })""",
    )
    no_horizontal_overflow = (
        max(measurements["document"], measurements["body"])
        <= measurements["viewport"] + 1
    )
    assert no_horizontal_overflow, (
        f"Overflow horizontal: {measurements}; "
        f"estado da página: {capture_page_state(page)}"
    )


def assert_content_reachable_above_mobile_nav(page, locator):
    if page.viewport_size["width"] >= DESKTOP_BREAKPOINT:
        return
    locator.scroll_into_view_if_needed()
    locator_box = locator.bounding_box()
    navigation = page.locator('nav[aria-label="Navegação principal"]').last
    expect(navigation).to_be_visible()
    navigation_box = navigation.bounding_box()
    assert locator_box is not None
    assert navigation_box is not None
    overlap = locator_box["y"] + locator_box["height"] - navigation_box["y"]
    if overlap > 0:
        page.evaluate("(distance) => window.scrollBy(0, distance)", overlap + 8)
        locator_box = locator.bounding_box()
        navigation_box = navigation.bounding_box()
        assert locator_box is not None
        assert navigation_box is not None
    action_is_above_navigation = (
        locator_box["y"] + locator_box["height"] <= navigation_box["y"]
    )
    assert action_is_above_navigation, (
        f"Conteúdo encoberto pela navegação fixa: ação={locator_box}, "
        f"navegação={navigation_box}; "
        f"estado={capture_page_state(page)}"
    )
