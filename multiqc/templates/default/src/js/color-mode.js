/* Native LSMC theme controller for standalone MultiQC reports. */

(() => {
  "use strict";

  const themeNames = ["original", "lsmc", "dark", "light", "nosee", "tacky"];
  const productionEnvironments = ["prod", "production", "clinical"];

  const normalizeTheme = (value) => {
    const theme = String(value || "").trim().toLowerCase();
    return themeNames.includes(theme) ? theme : "lsmc";
  };

  const tackyAllowed = () => {
    const html = document.documentElement;
    return html.dataset.allowTacky === "true" || !productionEnvironments.includes(html.dataset.lsmcEnvironment || "");
  };

  const storageKey = () => `lsmc.theme.${document.documentElement.dataset.lsmcService || "multiqc"}`;

  const getStoredTheme = () => {
    try {
      const value = localStorage.getItem(storageKey());
      return value === null ? null : normalizeTheme(value);
    } catch (_error) {
      return null;
    }
  };

  const setStoredTheme = (theme) => {
    try {
      localStorage.setItem(storageKey(), theme);
    } catch (_error) {
      // The report remains usable when browser storage is unavailable.
    }
  };

  const resolveTheme = (requested) => {
    const normalized = normalizeTheme(requested);
    if (normalized === "tacky" && !tackyAllowed()) {
      console.warn("LSMC theme contract prevented the Tacky theme in a production-like environment.");
      return "lsmc";
    }
    return normalized;
  };

  const setTheme = (requested, persist = false) => {
    const theme = resolveTheme(requested);
    const html = document.documentElement;
    html.dataset.theme = theme;
    html.dataset.bsTheme = ["lsmc", "dark"].includes(theme) ? "dark" : "light";
    if (persist) setStoredTheme(theme);
    return theme;
  };

  const showActiveTheme = (requested, focus = false) => {
    const theme = resolveTheme(requested);
    const switcher = document.querySelector("#bd-theme");
    if (!switcher) return;

    const activeIcon = switcher.querySelector(".theme-icon-active");
    let activeButton = null;
    document.querySelectorAll("[data-theme-value]").forEach((button) => {
      const active = button.dataset.themeValue === theme;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
      button.querySelector(".check-icon")?.classList.toggle("d-none", !active);
      if (active) activeButton = button;
    });

    if (activeButton && activeIcon) {
      const icon = activeButton.querySelector(".me-2");
      if (icon) activeIcon.innerHTML = icon.innerHTML;
      switcher.setAttribute("aria-label", `Theme (${activeButton.textContent.trim()})`);
    }
    if (focus) switcher.focus();
  };

  const configuredDefault = normalizeTheme(window.mqc_config?.lsmc_default_theme || "lsmc");
  const initialTheme = setTheme(getStoredTheme() || configuredDefault);

  window.LSMCThemeContract = { themeNames, normalizeTheme, setTheme, tackyAllowed };

  window.addEventListener("DOMContentLoaded", () => {
    showActiveTheme(initialTheme);
    document.querySelectorAll("[data-theme-value]").forEach((button) => {
      button.addEventListener("click", () => {
        const theme = setTheme(button.dataset.themeValue, true);
        showActiveTheme(theme, true);
      });
    });
  });
})();
