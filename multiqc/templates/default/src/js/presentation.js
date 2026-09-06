/* Presentation is data; scientific state is never changed here. */
window.addEventListener("DOMContentLoaded", () => {
  const payload = window.MQCPresentation;
  if (!payload || payload.schema_version !== "multiqc-presentation-v1") throw new Error("Missing or invalid MultiQC presentation sidecar");
  const root = new URL(window.MQCBundle?.entry || window.location.href, window.location.href);
  const linkUrl = (value) => {
    const mapping = window.MQCBundle?.url_map;
    if (mapping && Object.hasOwn(mapping, value)) return mapping[value];
    return /^https?:\/\//i.test(value) ? value : new URL(value, root).href;
  };
  const addNavigation = (id, title) => {
    const nav = document.querySelector(".mqc-nav");
    if (!nav || nav.querySelector(`[data-presentation-nav="${id}"]`)) return;
    const item = document.createElement("li");
    const a = document.createElement("a");
    a.dataset.presentationNav = id; a.className = "nav-l1";
    a.href = `#${id}`; a.textContent = title; item.append(a); nav.prepend(item);
  };
  if (payload.context) {
    document.getElementById("report-context").hidden = false;
    document.getElementById("report-context-title").textContent = payload.context.title;
    const body = document.getElementById("report-context-content");
    body.innerHTML = payload.context.html;
    body.querySelectorAll("a[href]").forEach((a) => { a.href = linkUrl(a.getAttribute("href")); });
    addNavigation("report-context", payload.context.title);
  }
  if (payload.links?.items.length) {
    document.getElementById("report-links").hidden = false;
    document.getElementById("report-links-title").textContent = payload.links.title;
    const list = document.getElementById("report-links-items");
    payload.links.items.forEach((item) => {
      const li = document.createElement("li"), a = document.createElement("a");
      a.textContent = item.label; a.href = linkUrl(item.url); li.append(a);
      if (item.description) li.append(document.createTextNode(`: ${item.description}`));
      list.append(li);
    });
    addNavigation("report-links", payload.links.title);
  }
  const brand = payload.style.brand;
  const old = document.querySelector(".lsmc-native-brand");
  if (old) {
    const link = document.createElement("a");
    if (brand.url) link.href = linkUrl(brand.url);
    const logo = document.createElement("img");
    logo.id = "mqc-presentation-logo";
    logo.src = document.documentElement.dataset.bsTheme === "dark" ? brand.logo_dark : brand.logo;
    logo.alt = brand.alt; logo.width = brand.width;
    link.append(logo); old.replaceChildren(link);
    document.querySelectorAll(".custom_logo").forEach((image) => image.closest(".float-end")?.remove());
  }
  let favicon = document.querySelector('link[rel="icon"]');
  if (!favicon) { favicon = document.createElement("link"); favicon.rel = "icon"; document.head.append(favicon); }
  favicon.href = brand.favicon;
  const css = document.createElement("style"); css.textContent = payload.style.css; document.head.append(css);
  window.addEventListener("beforeprint", () => {
    const logo = document.getElementById("mqc-presentation-logo"); if (logo) logo.src = brand.logo;
  });
  window.addEventListener("afterprint", () => {
    const logo = document.getElementById("mqc-presentation-logo");
    if (logo) logo.src = document.documentElement.dataset.bsTheme === "dark" ? brand.logo_dark : brand.logo;
  });
});
