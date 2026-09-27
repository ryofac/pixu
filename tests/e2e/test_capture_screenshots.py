from pathlib import Path
import pytest
from django.urls import reverse
from playwright.sync_api import expect
from .factories import create_user
from .helpers import app_url

pytestmark = pytest.mark.e2e

SCREENSHOT_DIR = Path("/app/docs/screenshots")

def test_capture_product_screenshots(page, live_server):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Desktop Landing
    page.set_viewport_size({"width": 1440, "height": 900})
    page.emulate_media(color_scheme="light")
    page.goto(app_url(live_server, reverse("home")))
    expect(page.get_by_role("heading", name="Combinar o rateio fica mais simples.")).to_be_visible()
    # Ilustração flutuante deve ser visível no desktop
    expect(page.get_by_text("Ana Pagou")).to_be_visible()
    expect(page.get_by_text("Conta Fechada")).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "landing_desktop_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "landing_desktop_dark.png"), full_page=True)

    # 2. Mobile Landing (390x844)
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_label("Aparência").select_option("light")
    expect(page.get_by_role("heading", name="Combinar o rateio fica mais simples.")).to_be_visible()
    # Em mobile, a ilustração flutuante deve estar oculta conforme product-design.md
    expect(page.get_by_text("Ana Pagou")).to_be_hidden()
    expect(page.get_by_role("heading", name="Cada pessoa entende a sua parte").first).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "landing_mobile_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(page.get_by_text("Ana Pagou")).to_be_hidden()
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "landing_mobile_dark.png"), full_page=True)

    # 3. Dashboard Desktop
    user = create_user(username="screenshot-user", name="Ryan", pix_key="ryan@example.com")
    page.set_viewport_size({"width": 1440, "height": 900})
    from .helpers import login_as
    login_as(page, live_server, user)
    expect(page).to_have_url(app_url(live_server, reverse("home")))
    expect(page.get_by_role("heading", name="Olá, Ryan")).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "dashboard_desktop_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "dashboard_desktop_dark.png"), full_page=True)

    # 4. Charges List
    page.goto(app_url(live_server, reverse("charges:list")))
    expect(page).to_have_url(app_url(live_server, reverse("charges:list")))
    expect(page.get_by_role("heading", name="Cobranças", exact=True)).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "charges_list_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "charges_list_dark.png"), full_page=True)

    # 5. Charge Create
    page.goto(app_url(live_server, reverse("charges:create")))
    expect(page).to_have_url(app_url(live_server, reverse("charges:create")))
    expect(page.get_by_role("heading", name="Nova cobrança", exact=True)).to_be_visible()
    expect(page.locator("#share-preview")).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "charge_create_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "charge_create_dark.png"), full_page=True)

    # 6. Invites
    page.goto(app_url(live_server, reverse("charges:invites")))
    expect(page).to_have_url(app_url(live_server, reverse("charges:invites")))
    expect(page.get_by_role("heading", name="Convites", exact=True)).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "invites_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "invites_dark.png"), full_page=True)

    # 7. User Detail Profile
    page.goto(app_url(live_server, reverse("accounts:detail", args=[user.username])))
    expect(page).to_have_url(app_url(live_server, reverse("accounts:detail", args=[user.username])))
    expect(page.get_by_role("heading", name="Meu perfil", exact=True)).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "profile_detail_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "profile_detail_dark.png"), full_page=True)

    # 8. Login Screen (Unauthenticated)
    page.context.clear_cookies()
    page.goto(app_url(live_server, reverse("account_login")))
    expect(page).to_have_url(app_url(live_server, reverse("account_login")))
    expect(page.get_by_role("heading", name="Entre na sua conta")).to_be_visible()
    expect(page.get_by_label("Nome de usuário")).to_be_visible()
    expect(page.get_by_label("Senha")).to_be_visible()
    page.get_by_label("Aparência").select_option("light")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "auth_login_light.png"), full_page=True)

    page.get_by_label("Aparência").select_option("dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(page.get_by_role("heading", name="Entre na sua conta")).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(SCREENSHOT_DIR / "auth_login_dark.png"), full_page=True)
