import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import expect

from pixu.charges.models import Charge
from pixu.charges.models import Participation

from .factories import create_user
from .helpers import app_url
from .helpers import assert_content_reachable_above_mobile_nav
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as
from .helpers import wait_for_htmx_response

pytestmark = pytest.mark.e2e
User = get_user_model()


def test_charge_create_previews_150_rejects_invalid_and_persists_only_on_submit(page, live_server):
    creator = create_user(username="criador-e2e", name="Criador")
    invitee = create_user(username="convidado-e2e", name="Convidado")
    login_as(page, live_server, creator)
    page.goto(app_url(live_server, reverse("charges:create")))

    page.get_by_label("Título").fill("Jantar E2E")
    page.get_by_label(invitee.username).check()
    amount = page.get_by_label("Valor total em reais")
    wait_for_htmx_response(
        page,
        reverse("charges:preview"),
        lambda: amount.fill("não é um valor"),
    )
    localized_error = page.locator('#share-preview [role="status"]')
    expect(localized_error).to_contain_text("Informe um número.")
    expect(localized_error).not_to_contain_text("Enter a number")
    assert not Charge.objects.filter(title="Jantar E2E").exists()

    wait_for_htmx_response(
        page,
        reverse("charges:preview"),
        lambda: amount.fill("150,00"),
    )
    preview = page.locator("#share-preview")
    expect(preview.get_by_role("heading", name="Prévia do rateio")).to_be_visible()
    expect(preview).to_contain_text("150,00")
    expect(preview.get_by_role("textbox", name="Criador")).to_have_value("75")
    expect(preview.get_by_role("textbox", name="Convidado")).to_have_value("75")
    assert not Charge.objects.filter(title="Jantar E2E").exists()

    assert_content_reachable_above_mobile_nav(
        page,
        page.get_by_role("button", name="Criar cobrança", exact=True),
    )
    page.get_by_role("button", name="Criar cobrança", exact=True).click()

    expect(page.get_by_role("heading", name="Jantar E2E")).to_be_visible()
    charge = Charge.objects.get(title="Jantar E2E")
    assert charge.total_cents == 15_000
    assert charge.state == Charge.State.AWAITING_ACCEPTANCE
    assert charge.participations.filter(user=creator, share_cents=7_500).exists()
    assert charge.participations.filter(user=invitee, share_cents=7_500).exists()


@pytest.mark.parametrize("viewport", [(390, 844), (1440, 900)])
def test_charge_detail_pluralization_and_long_content_fit_viewport(page, live_server, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    creator = create_user(username="detalhe-e2e", name="Nome longo da pessoa responsável pela cobrança")
    participant = create_user(
        username="convidado-com-identificador-bem-longo-e2e",
        name="Participante com nome de exibição comprido para testar o cartão no celular",
    )
    single = Charge.objects.create(
        creator=creator,
        creditor=creator,
        title="Cobrança individual para conferir singular",
        total_cents=12_500,
        state=Charge.State.ACTIVE,
    )
    Participation.objects.create(
        charge=single,
        user=creator,
        share_cents=12_500,
        state=Participation.State.ACCEPTED,
    )
    long_title = ("Cobrança com descrição muito longa " + "para testar a quebra de linha " * 8)[:120]
    shared = Charge.objects.create(
        creator=creator,
        creditor=creator,
        title=long_title,
        description="Detalhe longo para garantir que o conteúdo não ultrapasse o cartão. " * 12,
        total_cents=15_000,
        state=Charge.State.AWAITING_ACCEPTANCE,
    )
    Participation.objects.create(
        charge=shared,
        user=creator,
        share_cents=7_500,
        state=Participation.State.ACCEPTED,
    )
    Participation.objects.create(
        charge=shared,
        user=participant,
        share_cents=7_500,
        state=Participation.State.PENDING,
    )
    login_as(page, live_server, creator)

    page.goto(app_url(live_server, reverse("charges:detail", args=[single.pk])))
    expect(page.get_by_text("1 pessoa", exact=True)).to_be_visible()
    assert_no_horizontal_overflow(page)

    page.goto(app_url(live_server, reverse("charges:detail", args=[shared.pk])))
    expect(page.get_by_text("2 pessoas", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name=shared.title)).to_be_visible()
    assert_no_horizontal_overflow(page)
    assert_content_reachable_above_mobile_nav(page, page.get_by_text("Pendente", exact=True).last)
