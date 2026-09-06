/* Configured native theme controller, shared by offline and single-file reports. */
(() => {
  "use strict";
  const style = window.MQCPresentation.style;
  const themeNames = Object.keys(style.themes);
  const storageKey = () => `lsmc.theme.${document.documentElement.dataset.lsmcService || "multiqc"}`;
  const normalizeTheme = (name) => {
    if (!themeNames.includes(name) || !style.menu.includes(name)) throw new Error(`Unavailable theme: ${name}`);
    return name;
  };
  const tackyAllowed = () => style.menu.includes("tacky");
  let appliedTokens = [];
  const setTheme = (requested, persist = false) => {
    const name = normalizeTheme(requested);
    const html = document.documentElement;
    html.dataset.theme = name;
    html.dataset.bsTheme = style.themes[name].mode;
    appliedTokens.forEach((token) => html.style.removeProperty(token));
    const tokens = style.themes[name].tokens;
    Object.entries(tokens).forEach(([token, value]) => html.style.setProperty(token, value));
    appliedTokens = Object.keys(tokens);
    if (persist) {
      try { localStorage.setItem(storageKey(), name); } catch (error) { console.warn("Theme preference storage unavailable", error); }
    }
    document.querySelectorAll("[data-theme-value]").forEach((button) => {
      button.classList.toggle("active", button.dataset.themeValue === name);
      button.setAttribute("aria-pressed", String(button.dataset.themeValue === name));
    });
    const logo = document.getElementById("mqc-presentation-logo");
    if (logo) logo.src = style.themes[name].mode === "dark" ? style.brand.logo_dark : style.brand.logo;
    document.dispatchEvent(new CustomEvent("mqc-theme-changed", { detail: name }));
    return name;
  };
  let stored = null;
  try {
    stored = localStorage.getItem(storageKey());
    if (stored && !style.menu.includes(stored)) {
      console.warn(`Stored theme '${stored}' is no longer available; using configured default '${style.default_theme}'.`);
      localStorage.removeItem(storageKey());
      stored = null;
    }
  } catch (error) { console.warn("Theme preference storage unavailable", error); }
  const initial = setTheme(stored || style.default_theme);
  window.LSMCThemeContract = { themeNames, normalizeTheme, setTheme, tackyAllowed };
  window.addEventListener("DOMContentLoaded", () => {
    const switcher = document.getElementById("bd-theme");
    if (switcher) {
      switcher.parentElement.hidden = !style.show_switcher;
      const menu = switcher.parentElement.querySelector(".dropdown-menu");
      menu.replaceChildren();
      style.menu.forEach((name) => {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "dropdown-item d-flex align-items-center gap-2";
        button.dataset.themeValue = name;
        if (name === "lsmc") {
          const icon = document.createElement("img");
          icon.src = style.theme_icon; icon.alt = ""; icon.width = 24; icon.height = 24;
          button.append(icon);
        }
        button.append(document.createTextNode(style.themes[name].label));
        button.addEventListener("click", () => setTheme(name, true));
        item.append(button); menu.append(item);
      });
      const activeIcon = switcher.querySelector(".theme-icon-active");
      if (activeIcon) {
        const icon = document.createElement("img");
        icon.src = style.theme_icon; icon.alt = "Theme"; icon.width = 24; icon.height = 24;
        activeIcon.replaceChildren(icon);
      }
    }
    setTheme(initial);
  });
})();
