document.body.addEventListener("htmx:afterSwap", (event) => {
  const id = event.detail.target?.id;
  if (!id || !(id === "charge-content" || id.startsWith("invite-"))) return;

  const target = document.getElementById(id);
  const status = target?.querySelector("[data-focus-after-swap]");
  if (status) status.focus({ preventScroll: true });
});

document.body.addEventListener("pixu:pending-invites-updated", (event) => {
  const count = Number(event.detail.count || 0);
  document.querySelectorAll("[data-pending-invites-badge]").forEach((badge) => {
    badge.textContent = count ? String(count) : "";
    badge.setAttribute("aria-label", `${count} convites pendentes`);
    badge.classList.toggle("hidden", count === 0);
    badge.classList.toggle("grid", count > 0);
  });
});

document.body.addEventListener("input", (event) => {
  const search = event.target.closest("[data-invitee-search]");
  if (!search) return;

  const fieldset = search.closest("fieldset");
  const query = search.value.trim().toLocaleLowerCase("pt-BR");
  const options = [...fieldset.querySelectorAll("[data-invitee-option]")];
  let visibleCount = 0;

  options.forEach((option) => {
    const matches = option.textContent.trim().toLocaleLowerCase("pt-BR").includes(query);
    option.hidden = !matches;
    if (matches) visibleCount += 1;
  });

  const status = fieldset.querySelector("[data-invitee-search-status]");
  if (status) {
    status.textContent = visibleCount
      ? `${visibleCount} pessoas encontradas.`
      : "Nenhuma pessoa encontrada.";
  }
});

document.body.addEventListener("change", (event) => {
  const input = event.target.closest("[data-file-input]");
  if (!input) return;

  const container = input.closest("[data-file-upload]");
  const name = container?.querySelector("[data-file-name]");
  if (!name) return;

  const file = input.files?.[0];
  name.textContent = file?.name || name.dataset.emptyLabel;
  name.classList.toggle("text-pixu-ink", Boolean(file));
  name.classList.toggle("text-pixu-muted", !file);
});

document.body.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-text]");
  if (!button || !navigator.clipboard) return;

  await navigator.clipboard.writeText(button.dataset.copyText || "");
  const original = button.textContent;
  button.textContent = "Chave copiada";
  window.setTimeout(() => {
    button.textContent = original;
  }, 1800);
});

const THEME_PREFERENCE_KEY = "pixu-theme-preference";
const THEME_PREFERENCES = ["light", "dark", "system"];
const systemThemeQuery = window.matchMedia?.("(prefers-color-scheme: dark)");

function applyThemePreference(preference, persist = true) {
  if (!THEME_PREFERENCES.includes(preference)) preference = "system";

  const resolvedTheme =
    preference === "system"
      ? systemThemeQuery?.matches
        ? "dark"
        : "light"
      : preference;
  const root = document.documentElement;
  root.dataset.themePreference = preference;
  root.dataset.theme = resolvedTheme;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", resolvedTheme === "dark" ? "#0F172A" : "#FFF4F3");

  document.querySelectorAll("[data-theme-selector]").forEach((selector) => {
    selector.value = preference;
  });

  if (persist) {
    try {
      window.localStorage.setItem(THEME_PREFERENCE_KEY, preference);
    } catch {
      try {
        window.sessionStorage.setItem(THEME_PREFERENCE_KEY, preference);
      } catch {
        // Keep the choice active for the current page when all storage is blocked.
      }
    }
  }
}

document.addEventListener("change", (event) => {
  const selector = event.target.closest("[data-theme-selector]");
  if (selector) applyThemePreference(selector.value);
});

document.querySelectorAll("[data-theme-selector]").forEach((selector) => {
  selector.value = document.documentElement.dataset.themePreference || "system";
});

systemThemeQuery?.addEventListener("change", () => {
  if (document.documentElement.dataset.themePreference === "system") {
    applyThemePreference("system", false);
  }
});
