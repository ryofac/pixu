import pytest
from django.core.files.storage import default_storage
from django.db import connections
from django.urls import reverse
from playwright.sync_api import expect

from .helpers import app_url
from .helpers import assert_no_horizontal_overflow
from .helpers import capture_page_state

pytestmark = pytest.mark.e2e


def test_application_opens_with_isolated_test_services(page, live_server, settings):
    assert settings.DATABASES["default"]["HOST"] == "e2e-postgres"
    assert settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
    assert default_storage.__class__.__name__ == "FileSystemStorage"
    assert connections["default"].vendor == "postgresql"

    response = page.goto(app_url(live_server, reverse("account_login")))
    assert response is not None and response.status == 200
    expect(page.get_by_role("heading", name="Entre na sua conta")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("lang", "pt-br")
    assert_no_horizontal_overflow(page)

    state = capture_page_state(page)
    assert state["title"].endswith("Pixu")
