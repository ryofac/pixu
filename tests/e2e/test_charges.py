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


def test_invited_creditor_sees_pending_invitation_with_correct_terms(page, live_server):
    creator = create_user(username="ryan-criador-e2e", name="Ryan")
    creditor = create_user(username="ana-recebedora-e2e", name="Ana")
    other_invitee = create_user(username="bruno-convidado-e2e", name="Bruno")
    login_as(page, live_server, creator)
    page.goto(app_url(live_server, reverse("charges:create")))

    page.get_by_label("Título").fill("Jantar com recebedora convidada")
    page.get_by_label("Valor total em reais").fill("120,00")
    wait_for_htmx_response(
        page,
        reverse("charges:preview"),
        lambda: page.locator(
            f'input[name="invitees"][value="{creditor.pk}"]',
        ).check(),
    )
    wait_for_htmx_response(
        page,
        reverse("charges:preview"),
        lambda: page.locator(
            f'input[name="invitees"][value="{other_invitee.pk}"]',
        ).check(),
    )
    page.get_by_label("Quem recebe").select_option(value=str(creditor.pk))
    preview = page.locator("#share-preview")
    expect(preview.get_by_role("textbox", name="Ryan")).to_have_value("40")
    expect(preview.get_by_role("textbox", name="Ana")).to_have_value("40")
    expect(preview.get_by_role("textbox", name="Bruno")).to_have_value("40")
    page.get_by_role("button", name="Criar cobrança", exact=True).click()

    expect(
        page.get_by_role("heading", name="Jantar com recebedora convidada"),
    ).to_be_visible()
    charge = Charge.objects.get(title="Jantar com recebedora convidada")
    assert charge.creditor == creditor
    assert charge.state == Charge.State.AWAITING_ACCEPTANCE
    invitation = charge.participations.get(user=creditor)
    assert invitation.state == Participation.State.PENDING
    assert invitation.share_cents == 4_000

    login_as(page, live_server, creditor)
    page.goto(app_url(live_server, reverse("charges:invites")))

    invite_card = page.locator(f"#invite-{invitation.pk}")
    expect(invite_card).to_be_visible()
    expect(invite_card.get_by_role("heading", name=charge.title)).to_be_visible()
    expect(invite_card).to_contain_text("Criada por Ryan")
    expect(invite_card).to_contain_text("Quem recebe: Ana")
    expect(invite_card).to_contain_text("Sua cota")
    expect(invite_card).to_contain_text("40,00")
    expect(
        invite_card.get_by_role("button", name="Aceitar participação"),
    ).to_be_visible()
    expect(
        invite_card.get_by_role("button", name="Recusar convite"),
    ).to_be_visible()


def test_charge_creation_respects_invitees_direct_inclusion_preference(page, live_server):
    creator = create_user(username="criador-inclusao-e2e", name="Criadora")
    participant = create_user(username="participante-optin-e2e", name="Participante")
    participant.allow_direct_charge_inclusion = True
    participant.save(update_fields=["allow_direct_charge_inclusion"])
    login_as(page, live_server, creator)
    page.goto(app_url(live_server, reverse("charges:create")))

    page.get_by_label("Título").fill("Cota sem convite individual")
    page.get_by_label("Valor total em reais").fill("80,00")
    page.get_by_label(participant.username).check()
    page.get_by_role("button", name="Criar cobrança", exact=True).click()

    expect(page.get_by_role("heading", name="Cota sem convite individual")).to_be_visible()
    charge = Charge.objects.get(title="Cota sem convite individual")
    participation = Participation.objects.get(charge=charge, user=participant)
    assert participation.state == Participation.State.ACCEPTED
    assert participation.accepted_at is not None
    assert charge.state == Charge.State.ACTIVE
    login_as(page, live_server, participant)
    invites_page = page.goto(app_url(live_server, reverse("charges:invites")))
    assert invites_page is not None and invites_page.status == 200
    expect(page.get_by_text("Cota sem convite individual", exact=True)).to_have_count(0)


@pytest.mark.parametrize("viewport", [(375, 844), (1024, 900)])
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
    assert_content_reachable_above_mobile_nav(
        page,
        page.get_by_text("Aguardando aceite", exact=True).last,
    )
