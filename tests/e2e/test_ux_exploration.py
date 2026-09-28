from pathlib import Path
import pytest
from django.urls import reverse
from playwright.sync_api import expect
from pixu.charges.services import cancel_charge, create_charge
from .factories import create_user, create_active_debt, create_pending_payment
from .helpers import app_url, login_as

pytestmark = pytest.mark.e2e

AUDIT_DIR = Path("/app/docs/screenshots/ux_audit")

def test_ux_exploratory_audit(page, live_server):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Setup users and test data
    creator = create_user(username="ana_ux", name="Ana Silva", pix_key="ana@pix.me")
    invitee1 = create_user(username="bruno_ux", name="Bruno Costa", pix_key="bruno@pix.me")
    invitee2 = create_user(username="carla_ux", name="Carla Souza", pix_key="carla@pix.me")

    # Cobrança ativa para teste visual de status
    create_charge(
        creator=creator,
        title="Cinema e Pipoca",
        total_cents=8000,
        invitee_ids=[],
        creditor_id=creator.pk,
        include_creator=True,
    )

    # Cobrança cancelada para teste visual de status
    cancelled = create_charge(
        creator=creator,
        title="Passeio de Barco",
        total_cents=25000,
        invitee_ids=[],
        creditor_id=creator.pk,
        include_creator=True,
    )
    cancel_charge(charge_id=cancelled.pk, actor=creator, reason="Previsão de chuva forte")

    # ==========================================
    # AUDIT STEP 1: DESKTOP CREATION FLOW (1440x900)
    # ==========================================
    page.set_viewport_size({"width": 1440, "height": 900})
    login_as(page, live_server, creator)

    # Dashboard Desktop
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "1_dashboard_desktop.png"), full_page=True)

    # Click on "Nova cobrança" in desktop sidebar
    page.locator("aside").get_by_role("link", name="Nova cobrança").click()
    page.wait_for_url(app_url(live_server, reverse("charges:create")))
    expect(page.get_by_role("heading", name="Nova cobrança")).to_be_visible()

    # Form Empty State Desktop
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "2_charge_form_empty_desktop.png"), full_page=True)

    # Fill form fields
    page.get_by_label("Título").fill("Almoço de Domingo")
    page.get_by_label("Descrição").fill("Restaurante da praia - conta dividida")
    page.get_by_label("Valor total em reais").fill("150,00") # R$ 150,00

    # Search for an invitee
    search_input = page.locator("#invitee-search")
    search_input.fill("bruno")
    page.wait_for_timeout(200)

    # Select Bruno
    bruno_label = page.locator("label[data-invitee-option]:has-text('bruno_ux')")
    expect(bruno_label).to_be_visible()
    bruno_label.click()

    # Clear search and select Carla
    search_input.fill("")
    page.wait_for_timeout(200)
    carla_label = page.locator("label[data-invitee-option]:has-text('carla_ux')")
    carla_label.click()

    # Trigger live preview
    page.wait_for_timeout(500)
    page.screenshot(path=str(AUDIT_DIR / "3_charge_form_filled_desktop.png"), full_page=True)

    # Submit charge
    page.get_by_role("button", name="Criar cobrança").click()
    page.wait_for_timeout(500)

    # We should be on the charge detail page
    expect(page.get_by_role("heading", name="Almoço de Domingo")).to_be_visible()
    page.screenshot(path=str(AUDIT_DIR / "4_charge_detail_desktop.png"), full_page=True)

    # ==========================================
    # AUDIT STEP 2: MOBILE CREATION FLOW (390x844)
    # ==========================================
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(app_url(live_server, reverse("home")))
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "5_dashboard_mobile.png"), full_page=True)

    # On mobile, go to charges list then create
    page.locator("nav[aria-label='Navegação principal']").get_by_role("link", name="Cobranças").click()
    page.wait_for_url(app_url(live_server, reverse("charges:list")))
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "6_charges_list_mobile.png"), full_page=True)

    # Click "+ Nova cobrança"
    page.get_by_role("link", name="Nova cobrança").click()
    page.wait_for_url(app_url(live_server, reverse("charges:create")))
    expect(page.get_by_role("heading", name="Nova cobrança")).to_be_visible()

    # Form Empty State Mobile
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "7_charge_form_empty_mobile.png"), full_page=True)

    # Check mobile scroll and form elements
    page.get_by_label("Título").fill("Churrasco no Sítio")
    page.get_by_label("Valor total em reais").fill("300,00")
    page.wait_for_timeout(300)

    # Select Bruno on mobile
    page.locator("label[data-invitee-option]:has-text('bruno_ux')").click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(AUDIT_DIR / "8_charge_form_filled_mobile.png"), full_page=True)

    # ==========================================
    # AUDIT STEP 3: INVITEE INTERACTION FLOW
    # ==========================================
    # Log in as Bruno to see invites
    page.set_viewport_size({"width": 390, "height": 844})
    login_as(page, live_server, invitee1)
    expect(page.get_by_role("heading", name="Olá, Bruno")).to_be_visible()

    # Go to Invites
    page.locator("nav[aria-label='Navegação principal']").get_by_role("link", name="Convites").click()
    page.wait_for_url(app_url(live_server, reverse("charges:invites")))
    expect(page.get_by_role("heading", name="Convites", exact=True)).to_be_visible()
    page.wait_for_timeout(300)
    page.screenshot(path=str(AUDIT_DIR / "9_invites_mobile.png"), full_page=True)
