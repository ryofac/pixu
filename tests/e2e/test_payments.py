import pytest
from django.urls import reverse
from playwright.sync_api import expect

from pixu.charges.models import Debt
from pixu.charges.models import Participation
from pixu.charges.services import accept_participation
from pixu.charges.services import create_charge
from pixu.settlements.models import Payment
from pixu.settlements.services import record_payment

from .factories import create_active_debt
from .factories import create_pending_payment
from .factories import create_user
from .helpers import app_url
from .helpers import assert_no_horizontal_overflow
from .helpers import login_as
from .helpers import wait_for_htmx_response

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("comprovante.pdf", "application/pdf"),
        ("comprovante.jpg", "image/jpeg"),
        ("comprovante.png", "image/png"),
    ],
)
def test_partial_payment_selects_receipt_and_allows_replacement_and_removal(
    page,
    live_server,
    filename,
    content_type,
):
    payer = create_user(username="pagador-e2e")
    receiver = create_user(username="recebedor-e2e", pix_key="recebedor@example.test")
    _charge, debt = create_active_debt(debtor=payer, creditor=receiver)
    login_as(page, live_server, payer)
    page.goto(app_url(live_server, reverse("settlements:record", args=[debt.pk])))

    expect(page.get_by_text("recebedor@example.test", exact=True)).to_be_visible()
    page.get_by_label("Valor enviado em reais").fill("25,00")
    file_input = page.get_by_label("Comprovante (opcional)")
    file_input.set_input_files(
        {
            "name": filename,
            "mimeType": content_type,
            "buffer": {
                "application/pdf": b"%PDF-1.7\nBrowser receipt\n%%EOF\n",
                "image/jpeg": b"\xff\xd8\xff\xd9",
                "image/png": b"\x89PNG\r\n\x1a\nsynthetic image data",
            }[content_type],
        },
    )
    expect(page.locator("[data-file-name]")).to_have_text(filename)

    wait_for_htmx_response(
        page,
        reverse("settlements:record", args=[debt.pk]),
        lambda: page.get_by_role("button", name="Registrar pagamento", exact=True).click(),
    )
    debt_card = page.locator(f"#debt-{debt.pk}")
    expect(debt_card.get_by_role("status")).to_contain_text(
        "Pagamento registrado e aguardando confirmação.",
    )
    payment = Payment.objects.get(debt=debt)
    assert payment.amount_cents == 2_500
    assert payment.receipt_original_name == filename
    assert payment.state == Payment.State.PENDING
    expect(debt_card).to_contain_text("Pendente")
    assert_no_horizontal_overflow(page)

    replacement = page.get_by_label("Novo comprovante")
    replacement.set_input_files(
        {
            "name": "comprovante-substituto.png",
            "mimeType": "image/png",
            "buffer": b"\x89PNG\r\n\x1a\nreplacement receipt",
        },
    )
    expect(page.locator("[data-file-name]")).to_have_text("comprovante-substituto.png")
    wait_for_htmx_response(
        page,
        reverse("settlements:receipt_update", args=[payment.pk]),
        lambda: page.get_by_role("button", name="Substituir comprovante", exact=True).click(),
    )
    expect(debt_card.get_by_role("status")).to_contain_text("Comprovante atualizado.")
    payment.refresh_from_db()
    assert payment.receipt_original_name == "comprovante-substituto.png"

    wait_for_htmx_response(
        page,
        reverse("settlements:receipt_delete", args=[payment.pk]),
        lambda: page.get_by_role("button", name="Remover comprovante", exact=True).click(),
    )
    expect(debt_card.get_by_role("status")).to_contain_text("Comprovante removido.")
    expect(debt_card.get_by_role("link", name="Abrir comprovante privado")).to_have_count(0)
    payment.refresh_from_db()
    assert not payment.receipt
    assert payment.receipt_original_name == ""


def test_receiver_decides_payment_and_only_payer_or_receiver_can_open_receipt(page, live_server):
    payer = create_user(username="pagador-privacidade-e2e")
    receiver = create_user(username="recebedor-privacidade-e2e")
    outsider = create_user(username="terceiro-privacidade-e2e")
    charge, debt = create_active_debt(debtor=payer, creditor=receiver)
    pending = create_pending_payment(
        debt=debt,
        payer=payer,
        with_receipt=True,
    )
    receipt_url = app_url(live_server, reverse("settlements:receipt", args=[pending.pk]))

    login_as(page, live_server, payer)
    page.goto(app_url(live_server, reverse("charges:detail", args=[charge.pk])))
    payer_card = page.locator(f"#debt-{debt.pk}")
    expect(payer_card.get_by_role("button", name="Confirmar recebimento", exact=True)).to_have_count(0)
    expect(payer_card.get_by_role("button", name="Rejeitar pagamento", exact=True)).to_have_count(0)
    expect(payer_card.get_by_role("button", name="Substituir comprovante", exact=True)).to_be_visible()
    expect(page.request.get(receipt_url)).to_be_ok()

    login_as(page, live_server, receiver)
    page.goto(app_url(live_server, reverse("charges:detail", args=[charge.pk])))
    receiver_card = page.locator(f"#debt-{debt.pk}")
    expect(receiver_card.get_by_role("button", name="Confirmar recebimento", exact=True)).to_be_visible()
    expect(receiver_card.get_by_role("button", name="Rejeitar pagamento", exact=True)).to_be_visible()
    expect(receiver_card.get_by_role("button", name="Substituir comprovante", exact=True)).to_have_count(0)
    expect(page.request.get(receipt_url)).to_be_ok()
    wait_for_htmx_response(
        page,
        reverse("settlements:confirm", args=[pending.pk]),
        lambda: receiver_card.get_by_role("button", name="Confirmar recebimento", exact=True).click(),
    )
    expect(page.locator("#charge-content > [data-focus-after-swap]")).to_contain_text(
        "Pagamento confirmado.",
    )
    expect(receiver_card).to_contain_text("Pix confirmado")
    pending.refresh_from_db()
    assert pending.state == Payment.State.CONFIRMED

    rejected = record_payment(debt_id=debt.pk, actor=payer, amount_cents=1_000)
    page.reload()
    receiver_card = page.locator(f"#debt-{debt.pk}")
    expect(receiver_card.get_by_role("button", name="Rejeitar pagamento", exact=True)).to_be_visible()
    wait_for_htmx_response(
        page,
        reverse("settlements:reject", args=[rejected.pk]),
        lambda: receiver_card.get_by_role("button", name="Rejeitar pagamento", exact=True).click(),
    )
    expect(page.locator("#charge-content > [data-focus-after-swap]")).to_contain_text(
        "Pagamento rejeitado; o valor voltou a ficar disponível.",
    )
    expect(receiver_card).to_contain_text("Rejeitado")
    rejected.refresh_from_db()
    assert rejected.state == Payment.State.REJECTED

    login_as(page, live_server, outsider)
    receipt_response = page.request.get(receipt_url)
    assert receipt_response.status == 403
    detail_response = page.goto(app_url(live_server, reverse("charges:detail", args=[charge.pk])))
    assert detail_response is not None and detail_response.status == 404


@pytest.mark.parametrize("viewport", [(390, 844), (1440, 900)])
def test_receiver_can_enable_auto_confirmation_for_one_debt(
    page,
    live_server,
    viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    payer = create_user(username=f"pagador-auto-{viewport[0]}")
    receiver = create_user(username=f"recebedor-auto-{viewport[0]}")
    charge, debt = create_active_debt(
        debtor=payer,
        creditor=receiver,
        amount_cents=5_000,
        title="Cota com confirmação configurável",
    )

    login_as(page, live_server, receiver)
    page.goto(app_url(live_server, reverse("charges:detail", args=[charge.pk])))
    page.locator("html").evaluate("element => element.dataset.theme = 'dark'")
    assert_no_horizontal_overflow(page)
    participant_row = page.locator(f"[data-participant-row='{debt.participation_id}']")
    participant_row.get_by_role("button", name="Detalhes e histórico").click()
    dialog = page.get_by_role("dialog")
    checkbox = dialog.get_by_role(
        "checkbox",
        name="Confirmar automaticamente pagamentos declarados",
    )
    expect(checkbox).not_to_be_checked()
    expect(
        dialog.get_by_text("O Pixu não verifica a transferência", exact=False),
    ).to_be_visible()
    wait_for_htmx_response(
        page,
        reverse("settlements:auto_confirm", args=[debt.pk]),
        lambda: (
            checkbox.check(),
            dialog.get_by_role(
                "button",
                name="Salvar preferência desta cota",
            ).click(),
        ),
    )
    expect(page.locator("#charge-content > [data-focus-after-swap]")).to_contain_text(
        "Preferência atualizada.",
    )
    debt.refresh_from_db()
    assert debt.auto_confirm_payments
    assert_no_horizontal_overflow(page)

    login_as(page, live_server, payer)
    page.goto(app_url(live_server, reverse("settlements:record", args=[debt.pk])))
    page.locator("html").evaluate("element => element.dataset.theme = 'light'")
    expect(page.get_by_text("este pagamento declarado será confirmado", exact=False)).to_be_visible()
    page.get_by_label("Valor enviado em reais").fill("20,00")
    wait_for_htmx_response(
        page,
        reverse("settlements:record", args=[debt.pk]),
        lambda: page.get_by_role("button", name="Registrar pagamento", exact=True).click(),
    )
    expect(page.locator(f"#debt-{debt.pk} [role='status']")).to_contain_text(
        "Pagamento registrado e confirmado automaticamente no Pixu.",
    )
    payment = Payment.objects.get(debt=debt)
    assert payment.state == Payment.State.CONFIRMED
    assert payment.confirmation_source == Payment.ConfirmationSource.AUTOMATIC
    assert_no_horizontal_overflow(page)


@pytest.mark.parametrize("viewport", [(390, 844), (1440, 900)])
def test_receiver_hierarchy_reorders_after_a_manual_confirmation(
    page,
    live_server,
    viewport,
):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    receiver = create_user(username=f"recebedor-hierarquia-{viewport[0]}")
    pending_payer = create_user(username=f"ana-hierarquia-{viewport[0]}", name="Ana")
    open_payer = create_user(username=f"bruno-hierarquia-{viewport[0]}", name="Bruno")
    charge = create_charge(
        creator=receiver,
        title="Conta com atenção",
        total_cents=30_000,
        invitee_ids=[pending_payer.pk, open_payer.pk],
        include_creator=False,
    )
    pending_participation = Participation.objects.get(
        charge=charge,
        user=pending_payer,
    )
    open_participation = Participation.objects.get(charge=charge, user=open_payer)
    accept_participation(participation_id=pending_participation.pk, actor=pending_payer)
    accept_participation(participation_id=open_participation.pk, actor=open_payer)
    pending_debt = Debt.objects.get(participation=pending_participation)
    pending_payment = record_payment(
        debt_id=pending_debt.pk,
        actor=pending_payer,
        amount_cents=15_000,
    )

    login_as(page, live_server, receiver)
    page.goto(app_url(live_server, reverse("charges:detail", args=[charge.pk])))
    expect(page.get_by_role("heading", name="Participantes e cotas")).to_be_visible()
    group = page.locator("[aria-labelledby='participant-group-pixu']")
    rows = group.locator("[data-participant-row]")
    expect(rows.nth(0)).to_contain_text("Ana")
    expect(rows.nth(1)).to_contain_text("Bruno")
    expect(rows.nth(0).get_by_role(
        "button",
        name="Confirmar recebimento",
        exact=True,
    )).to_be_visible()
    assert_no_horizontal_overflow(page)

    wait_for_htmx_response(
        page,
        reverse("settlements:confirm", args=[pending_payment.pk]),
        lambda: rows.nth(0).get_by_role(
            "button",
            name="Confirmar recebimento",
            exact=True,
        ).click(),
    )
    status = page.locator("#charge-content > [data-focus-after-swap]")
    expect(status).to_contain_text("Pagamento confirmado.")
    expect(status).to_be_focused()
    rows = group.locator("[data-participant-row]")
    expect(rows.nth(0)).to_contain_text("Bruno")
    expect(rows.nth(1)).to_contain_text("Ana")
    expect(rows.nth(1)).to_contain_text("Pix confirmado")
    expect(
        rows.nth(1).get_by_role("button", name="Confirmar recebimento"),
    ).to_have_count(0)
    assert_no_horizontal_overflow(page)
