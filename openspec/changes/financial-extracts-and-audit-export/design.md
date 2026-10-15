## Context

See `proposal.md` for the motivation and `specs/` for the approved behavior. The authenticated dashboard currently calculates balances in `pixu/dashboard/services.py`; payments and compensations are separate records in `pixu/settlements`, and charge details already enforce access to each debt. The `Payment` record distinguishes registration, confirmation, source and current state; `Compensation` is one record referencing both debts it reduces. A cancelled charge changes its payments to `REVOKED` while retaining `confirmed_at` for payments that had been confirmed.

The app renders Django templates and uses server-side authorization. Its Python runtime is pinned to 3.14, and local and production images have separate dependency installation stages. There is no shared extract route or PDF renderer today. Existing debt math treats pending payments as reserved, not as a reduction in the open balance.

## Goals / Non-Goals

**Goals:**

- Reuse the existing debt, payment and compensation records as the source of truth; do not introduce a parallel ledger or recalculate money with floating point.
- Keep each extract and file scoped to financial records the authenticated person is allowed to see.
- Keep dashboard previews compact and balances separated by direction.
- Render normal pages with Django templates and GET forms so search, date filters and pagination work without JavaScript.
- Produce CSV and PDF from the same authorized, filtered result set.

**Non-Goals:**

- Changing payment confirmation, cancellation or compensation behavior.
- Including private receipt files or public receipt URLs in downloads.
- Treating guest-entered names as verified identities or merging separate guest participations by matching names.
- Adding a public API, SPA, bank integration, background export service or a new financial-event database model.

## Decisions

### Query and balance source

Create a dedicated Django app at `pixu/extracts` for read-only extract queries, presentation, filters, exports, templates and URL routing. It reads `Debt` from charges and `Payment`/`Compensation` from settlements, reusing the shared cent-based balance calculation in `pixu/settlements/services.py`; settlements does not import the extracts app. Dashboard previews use the same extract query layer. **A pagar** is scoped by `Debt.debtor_id`; **A receber** by `Debt.creditor_id`. Both require accepted participation, an active charge and positive open balance. Open balance is original cents minus currently confirmed payment cents and compensation cents applied to either side of the debt; pending payments do not reduce it. Batch payment and compensation aggregation for the dashboard preview and paginated pages to avoid one query per debt.

The dashboard preview is separate for each direction: up to five counterparties ordered by their oldest debt with positive balance, with the sum of all positive open balances in that direction. Account holders group by user ID. A guest with no account is keyed by its participation ID, shown with the name available for that charge, and never merged with another guest based on text. Keep the compensation suggestion alongside an eligible payable debt; remove the global potential card.

A lista autenticada `/charges/` usa a mesma prioridade financeira: cobranças com dívidas abertas positivas são separadas em **A pagar primeiro** e **A receber primeiro**, ordenadas pela dívida aberta mais antiga de cada cobrança. Se uma cobrança a receber contiver várias dívidas abertas, ela aparece uma vez e mostra a soma desses saldos. As demais cobranças visíveis, incluindo aguardando aceite, quitadas e canceladas, permanecem em **Outras cobranças**, das mais recentes para as mais antigas. Os cartões continuam abrindo o detalhe existente e autorizado da cobrança.

### Server-rendered routes and filters

Add authenticated GET pages and download routes under the app's own `extracts` namespace, mounted at `/extracts/`. Keep the three extract query builders independent from presentation so HTML, CSV and PDF receive the same authorized records. Use query parameters for person/title search and, for **Já pago**, inclusive start and end dates interpreted with Django's configured timezone. Paginate only the HTML page and preserve query parameters in pagination links and download links. Exports ignore the current page and process all rows matching the current filters.

**Já pago** is a normalized read-only timeline over `Payment` and `Compensation`. Include confirmed payments and applied compensations that reduce the authenticated person's payable debts. Include a payment with current state `REVOKED` only when `confirmed_at` is present, including when charge cancellation revoked it, so the formerly confirmed event remains visible but is excluded from paid totals; do not include a revoked payment that was never confirmed. Use `confirmed_at` for a payment's effective date and `Compensation.created_at` for a compensation. Represent each compensation once per viewer and expose both linked charges. Sort by effective date descending with a stable event-type and primary-key tie-breaker.

### CSV and PDF generation

Generate CSV with Python's `csv` module, UTF-8 BOM and semicolon delimiter for pt-BR spreadsheet defaults. Include stable debt/payment/compensation identifiers and exact integer cent values in the export data. Escape free-text fields for CSV and neutralize leading spreadsheet formula characters; quoting alone does not prevent formula execution.

Generate the styled PDF from a dedicated Django print template with WeasyPrint. This reuses server-rendered, auto-escaped content and print CSS; a separate ReportLab layout would duplicate the brand and table design. Pin the dependency in `pyproject.toml`/`uv.lock` and install the needed Pango runtime libraries in local and production Django images. The official [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) lists Python 3.10 or newer and Pango for Linux; the implementation must confirm the selected release works with this project's Python 3.14 image.

Give the PDF a title, generation time, extract type, active filters, totals, repeated table headings and page numbers. Use the existing Sakura tokens and a restrained print palette. Do not fetch arbitrary URLs while rendering; use a restricted URL fetcher or inline/local whitelisted assets only. Show whether a receipt exists, but do not embed it or generate an externally usable receipt link.

### Authorization and privacy

Enforce the same `debtor`/`creditor` scoping in the service that builds each result, not only in templates or links. A charge creator who is not a financial party does not inherit access to these extracts. The creditor can see a guest debt on **A receber** through the existing creditor relation; the guest's name remains attached only to its participation. Apply these checks to both conventional requests and downloads. Keep all monetary calculations as integer cents and render currency formatting only at the presentation boundary.

## Risks / Trade-offs

- [Different event models have different dates and statuses] → Normalize them into a read-only presentation row while retaining event type, stable source ID, effective date and current state.
- [A revoked payment may mean it was never confirmed] → Include it in **Já pago** only if the preserved `confirmed_at` field is set; show the revoked state and exclude it from totals.
- [Repeated guest names can refer to different people] → Group guests by participation ID, following the product rule that a self-declared name is not identity verification.
- [PDF support adds image size and native libraries] → Pin WeasyPrint, install only required runtime packages in Django images, and verify build/runtime compatibility with Python 3.14 before release.
- [A renderer could fetch remote resources or expose private data] → Use escaped template values, a restricted resource fetcher, and no receipt content or private storage URLs in the PDF.
- [A large history can make PDF generation slow or memory-intensive] → Paginate the page, keep CSV streaming where practical, select only needed columns, and profile PDF generation with representative long histories during implementation.
- [Spreadsheet formulas can run from untrusted text] → Apply formula-safe serialization to user-controlled CSV text while preserving numeric columns as numeric output.

## Migration Plan

No database migration is required. Add the pinned renderer dependency and its local/production runtime libraries, build and deploy the Django image, then expose the new authenticated GET routes. Rollback consists of reverting the application and image dependency changes; it does not alter payment, compensation or charge data.
