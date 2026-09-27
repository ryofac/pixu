(() => {
  const root = document.documentElement;
  let preference = "system";

  try {
    const saved = window.localStorage.getItem("pixu-theme-preference");
    if (["light", "dark", "system"].includes(saved)) preference = saved;
  } catch {
    try {
      const saved = window.sessionStorage.getItem("pixu-theme-preference");
      if (["light", "dark", "system"].includes(saved)) preference = saved;
    } catch {
      // The system preference remains the fallback when browser storage is blocked.
    }
  }

  let systemTheme = "light";
  try {
    if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
      systemTheme = "dark";
    }
  } catch {
    // Older or restricted browsers use the accessible light fallback.
  }

  root.dataset.themePreference = preference;
  root.dataset.theme = preference === "system" ? systemTheme : preference;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", root.dataset.theme === "dark" ? "#0F172A" : "#FFF4F3");
})();
