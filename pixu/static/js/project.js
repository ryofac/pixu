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
  const shareBtn = event.target.closest("[data-share-url]");
  if (shareBtn) {
    const url = shareBtn.dataset.shareUrl || "";
    const title = shareBtn.dataset.shareTitle || "Pixu";
    const text = shareBtn.dataset.shareText || "";
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url });
        return;
      } catch (err) {
        if (err.name === "AbortError") return;
      }
    }
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(url);
      const original = shareBtn.textContent;
      shareBtn.textContent = shareBtn.dataset.copiedLabel || "Link copiado!";
      window.setTimeout(() => {
        shareBtn.textContent = original;
      }, 1800);
    }
    return;
  }

  const copyBtn = event.target.closest("[data-copy-text]");
  if (!copyBtn) return;

  const textToCopy = copyBtn.dataset.copyText || "";
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(textToCopy);
  } else {
    const ta = document.createElement("textarea");
    ta.value = textToCopy;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
  const original = copyBtn.textContent;
  copyBtn.textContent = copyBtn.dataset.copiedLabel || "Copiado!";
  window.setTimeout(() => {
    copyBtn.textContent = original;
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

const installPrompt = document.querySelector("[data-install-prompt]");
const installAction = installPrompt?.querySelector("[data-install-action]");
const installDismiss = installPrompt?.querySelector("[data-install-dismiss]");
const installMessage = installPrompt?.querySelector("[data-install-message]");
const INSTALL_DISMISS_KEY = "pixu-install-prompt-dismissed-at";
const INSTALL_DISMISS_TTL = 7 * 24 * 60 * 60 * 1000;
let deferredInstallPrompt = null;

function isStandaloneApp() {
  return window.matchMedia?.("(display-mode: standalone)").matches || window.navigator.standalone === true;
}

function isMobileInstallViewport() {
  return window.matchMedia?.("(max-width: 639px)").matches ?? false;
}

function isIosDevice() {
  return /iPad|iPhone|iPod/.test(window.navigator.userAgent)
    || (window.navigator.platform === "MacIntel" && window.navigator.maxTouchPoints > 1);
}

function wasInstallPromptDismissed() {
  try {
    const dismissedAt = Number(window.localStorage.getItem(INSTALL_DISMISS_KEY));
    return dismissedAt > Date.now() - INSTALL_DISMISS_TTL;
  } catch {
    return false;
  }
}

function dismissInstallPrompt() {
  try {
    window.localStorage.setItem(INSTALL_DISMISS_KEY, String(Date.now()));
  } catch {
    // A blocked storage API must not prevent the prompt from closing.
  }
  if (installPrompt) {
    installPrompt.hidden = true;
    installPrompt.classList.add("hidden");
  }
}

function showInstallPrompt({ ios = false } = {}) {
  if (!installPrompt || !isMobileInstallViewport() || isStandaloneApp() || wasInstallPromptDismissed()) return;

  if (installMessage) {
    installMessage.textContent = ios
      ? "No Safari, toque em Compartilhar e depois em Adicionar à Tela de Início."
      : "Tenha suas cobranças sempre à mão, com acesso rápido pelo celular.";
  }
  if (installAction) installAction.hidden = ios;
  installPrompt.hidden = false;
  installPrompt.classList.remove("hidden");
}

installDismiss?.addEventListener("click", dismissInstallPrompt);
installAction?.addEventListener("click", async () => {
  if (!deferredInstallPrompt) return;

  const promptEvent = deferredInstallPrompt;
  deferredInstallPrompt = null;
  try {
    await promptEvent.prompt();
    const choice = await promptEvent.userChoice;
    if (choice.outcome === "dismissed") dismissInstallPrompt();
    else if (installPrompt) {
      installPrompt.hidden = true;
      installPrompt.classList.add("hidden");
    }
  } catch {
    if (installPrompt) {
      installPrompt.hidden = true;
      installPrompt.classList.add("hidden");
    }
  }
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  showInstallPrompt();
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  if (installPrompt) {
    installPrompt.hidden = true;
    installPrompt.classList.add("hidden");
  }
});

if (isIosDevice()) {
  window.setTimeout(() => showInstallPrompt({ ios: true }), 1200);
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(() => {
      // Installation remains optional when service workers are unavailable.
    });
  });
}
