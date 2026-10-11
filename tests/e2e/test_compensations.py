from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from pixu.charges.models import Charge
from pixu.charges.models import Debt
from pixu.settlements.models import Compensation
from pixu.settlements.services import payment_balance

from .factories import create_user
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as
from .helpers import wait_for_htmx_response

if TYPE_CHECKING:
    from pixu.accounts.models import User

pytestmark = pytest.mark.e2e
VIEWPORTS = [(390, 844), (1440, 900)]
COMPENSATION_AMOUNT_CENTS = 2_000
DEBT_REMAINDER_CENTS = 3_000
RECIPROCAL_REMAINDER_CENTS = 1_000


@dataclass(frozen=True)
class ChargeCreation:
    creator: User
    creditor: User
    title: str
    total: str


@dataclass(frozen=True)
class ReciprocalScenario:
    debtor: User
    debt_charge: Charge
    debt: Debt
    reciprocal_charge: Charge
    reciprocal_debt: Debt


def create_charge_through_ui(page, live_server, scenario: ChargeCreation):
    login_as(page, live_server, scenario.creator)
    page.goto(app_url(live_server, reverse("charges:create")))
    page.get_by_label("Título").fill(scenario.title)
    page.get_by_label("Valor total em reais").fill(scenario.total)
    page.get_by_label("Quem recebe").select_option(value=str(scenario.creditor.pk))
    page.get_by_role("button", name="Criar cobrança", exact=True).click()

    charge = Charge.objects.get(title=scenario.title)
    expect(page).to_have_url(
        app_url(live_server, reverse("charges:detail", args=[charge.pk])),
    )
    assert charge.state == Charge.State.ACTIVE
    return charge, Debt.objects.get(participation__charge=charge)


def create_reciprocal_scenario(page, live_server, suffix: str):
    debtor = create_user(username=f"ana-comp-e2e-{suffix}", name="Ana")
    creditor = create_user(username=f"ryan-comp-e2e-{suffix}", name="Ryan")
    debt_charge, debt = create_charge_through_ui(
        page,
        live_server,
        ChargeCreation(
            creator=debtor,
            creditor=creditor,
            title=f"Jantar recíproco {suffix}",
            total="50,00",
        ),
    )
    reciprocal_charge, reciprocal_debt = create_charge_through_ui(
        page,
        live_server,
        ChargeCreation(
            creator=creditor,
            creditor=debtor,
            title=f"Cinema recíproco {suffix}",
            total="30,00",
        ),
    )
    return ReciprocalScenario(
        debtor=debtor,
        debt_charge=debt_charge,
        debt=debt,
        reciprocal_charge=reciprocal_charge,
        reciprocal_debt=reciprocal_debt,
    )


def assert_compensation_after_reload(page, live_server, scenario):
    event = Compensation.objects.get()
    assert event.debt_id == scenario.debt.pk
    assert event.reciprocal_debt_id == scenario.reciprocal_debt.pk
    assert event.amount_cents == COMPENSATION_AMOUNT_CENTS
    assert event.initiated_by_id == scenario.debtor.pk
    assert payment_balance(scenario.debt).open_cents == DEBT_REMAINDER_CENTS
    assert (
        payment_balance(scenario.reciprocal_debt).open_cents
        == RECIPROCAL_REMAINDER_CENTS
    )
    expect(page.locator(f"#debt-{scenario.debt.pk}")).to_contain_text("Compensado")
    expect(
        page.locator(f"#debt-{scenario.debt.pk}"),
    ).to_contain_text("Histórico de compensações")
    expect(page.locator(f"#debt-{scenario.debt.pk}")).to_contain_text(
        scenario.reciprocal_charge.title,
    )

    scenario.debt_charge.refresh_from_db()
    scenario.reciprocal_charge.refresh_from_db()
    assert scenario.debt_charge.locked_at is not None
    assert scenario.reciprocal_charge.locked_at is not None

    page.reload()
    debt_card = page.locator(f"#debt-{scenario.debt.pk}")
    expect(debt_card.locator("dl").first.locator("dd").nth(0)).to_have_text("30,00")
    expect(debt_card).to_contain_text("Histórico de compensações")

    page.goto(
        app_url(
            live_server,
            reverse("charges:detail", args=[scenario.reciprocal_charge.pk]),
        ),
    )
    reciprocal_debt_card = page.locator(f"#debt-{scenario.reciprocal_debt.pk}")
    expect(
        reciprocal_debt_card.locator("dl").first.locator("dd").nth(0),
    ).to_contain_text("10,00")
    expect(reciprocal_debt_card).to_contain_text("Histórico de compensações")
    assert_no_horizontal_overflow(page)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_partial_compensation_from_ui_updates_both_debts_and_history(
    page,
    live_server,
    viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    scenario = create_reciprocal_scenario(page, live_server, str(viewport[0]))
    login_as(page, live_server, scenario.debtor)
    page.goto(
        app_url(
            live_server,
            reverse("charges:detail", args=[scenario.debt_charge.pk]),
        ),
    )
    assert_no_horizontal_overflow(page)

    debt_card = page.locator(f"#debt-{scenario.debt.pk}")
    heading = debt_card.get_by_role(
        "heading",
        name=f"Dívida inversa: {scenario.reciprocal_charge.title}",
    )
    expect(heading).to_be_visible()
    compensation_amount = page.get_by_label("Valor a compensar em reais")
    preview_path = (
        f"debts/{scenario.debt.pk}/compensations/"
        f"{scenario.reciprocal_debt.pk}/preview/"
    )
    with page.expect_response(
        lambda response: (
            preview_path in response.url and response.request.method == "GET"
        ),
    ):
        compensation_amount.fill("20,00")
    preview = page.locator(
        f"#compensation-preview-{scenario.debt.pk}-{scenario.reciprocal_debt.pk}",
    )
    expect(preview.locator("[data-compensation-preview-amount]")).to_have_text(
        "20,00",
    )
    expect(
        preview.locator("[data-compensation-preview-remaining]"),
    ).to_have_text("30,00")
    assert not Compensation.objects.exists()
    assert_content_reachable_above_mobile_nav(
        page,
        debt_card.get_by_role("button", name="Aceitar compensação", exact=True),
    )

    review_button = debt_card.get_by_role("button", name="Revisar valor", exact=True)
    apply_button = debt_card.get_by_role(
        "button",
        name="Aceitar compensação",
        exact=True,
    )
    compensation_amount.focus()
    page.keyboard.press("Tab")
    expect(review_button).to_be_focused()
    page.keyboard.press("Tab")
    expect(apply_button).to_be_focused()

    apply_path = (
        f"debts/{scenario.debt.pk}/compensations/"
        f"{scenario.reciprocal_debt.pk}/apply/"
    )
    wait_for_htmx_response(
        page,
        apply_path,
        lambda: page.keyboard.press("Enter"),
    )
    expect(page).to_have_url(
        app_url(
            live_server,
            reverse("charges:detail", args=[scenario.debt_charge.pk]),
        ),
    )
    assert_no_horizontal_overflow(page)
    assert_compensation_after_reload(page, live_server, scenario)
