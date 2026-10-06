import pytest
from django.urls import reverse
from playwright.sync_api import expect

from .helpers import app_url

pytestmark = pytest.mark.e2e


def test_mobile_install_prompt_appears_after_browser_install_event(page, live_server):
    page.goto(app_url(live_server, reverse("home")))

    manifest = page.locator('link[rel="manifest"]')
    expect(manifest).to_have_attribute("href", reverse("pwa_manifest"))

    page.evaluate(
        """() => {
          const event = new Event("beforeinstallprompt", { cancelable: true });
          event.prompt = () => Promise.resolve();
          event.userChoice = Promise.resolve({ outcome: "dismissed" });
          window.dispatchEvent(event);
        }""",
    )

    install_prompt = page.locator("[data-install-prompt]")
    expect(install_prompt).to_be_visible()
    expect(install_prompt).to_contain_text("Instale o Pixu")
    expect(install_prompt.get_by_role("button", name="Instalar app")).to_be_visible()
