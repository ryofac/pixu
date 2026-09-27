---
name: pixu-doc-screenshots
description: Capture and review deterministic Pixu UI screenshots for project documentation using the isolated Playwright E2E suite. Use when asked to save or refresh application screenshots in docs; not for production-browser screenshots.
---

# Pixu documentation screenshots

Capture the current Django UI through the repository's Playwright E2E test and save its evidence under `docs/screenshots/`. Treat the active OpenSpec change and `docs/product-design.md` as the source of truth for what should appear; screenshots document the implementation and are not a substitute for those decisions.

## Capture workflow

1. Read `AGENTS.md`, the relevant sections of `docs/product-design.md`, and the active OpenSpec change. Check `tests/e2e/test_capture_screenshots.py` for the current routes, assertions, viewport sizes, themes, and filenames before changing the capture matrix.
2. Build and capture with the repo's E2E recipe:

   ```sh
   just e2e tests/e2e/test_capture_screenshots.py
   ```

   The recipe builds local Tailwind assets and runs Chromium in the isolated `e2e` Compose service. The test writes to `/app/docs/screenshots`; Compose bind-mounts the repository at `/app`, so the resulting files appear in the local `docs/screenshots/` directory. No production service or authenticated personal browser session is needed.
3. Confirm the test passed, then inspect the generated images in `docs/screenshots/`. Check the changed screens at their intended viewport and theme, including clipping, text, contrast, and whether the page is in the expected authenticated state. A passing assertion alone does not establish visual quality.
4. Report which screenshots were created or refreshed and any visual issue that needs a product or implementation decision. Keep unrelated screenshots and worktree changes untouched.

## Current capture set

The current test captures full-page PNGs for:

- Landing: desktop `1440×900` and mobile `390×844`, each in light and dark themes.
- Authenticated dashboard, charges list, charge creation, invites, and profile: desktop, each in light and dark themes.
- Unauthenticated login: desktop, in light and dark themes.

The test's filenames are the canonical names (for example `landing_mobile_light.png` and `dashboard_desktop_dark.png`). Read the test rather than assuming this matrix is permanent. Other E2E coverage may test responsive behavior without saving screenshots.

The test uses a synthetic account created by `tests/e2e/factories.py`; login is performed by the test helper, then cookies are cleared before capturing the login page. Keep all captured data synthetic. Never put real account details, payment information, private receipts, secrets, or production data into documentation screenshots. The landing illustration's sample content is intentional product design; preserve it unless the user changes that direction.

## Updating the capture test

When a requested documentation view is missing or an approved UI change alters its expected state, update `tests/e2e/test_capture_screenshots.py` in the same scope: set the viewport and theme explicitly, assert the expected route and identifying content/state before capture, and use a stable descriptive filename. Preserve test isolation and avoid fixed waits when a deterministic visible-state assertion can establish readiness. Do not expand the screenshot matrix or change product UI merely because a capture would be convenient; follow the user's request and active product decisions.

Rerunning the test overwrites PNGs with matching names. Review the diff and `git status` before reporting; do not remove existing screenshots or other user changes as cleanup. Avoid committing screenshots unless the user asks to include them in a commit.
