/* Keep signed queries untouched; selector state and output anchors share the fragment. */
export const bundleFragment = (hash) => {
  if (!hash || hash === "#") return { section: null, state: null };
  if (!hash.startsWith("#mqc-state=")) return { section: decodeURIComponent(hash.slice(1)), state: null };
  const params = new URLSearchParams(hash.slice(1));
  return { section: params.get("section"), state: params.get("mqc-state") };
};

export const bundleHref = (href, state) => {
  const split = href.indexOf("#");
  const base = split < 0 ? href : href.slice(0, split);
  const section = split < 0 ? null : bundleFragment(href.slice(split)).section;
  return base + "#mqc-state=" + encodeURIComponent(JSON.stringify(state)) +
    (section ? "&section=" + encodeURIComponent(section) : "");
};

if (typeof window !== "undefined") {
  const scrollToOutput = () => {
    if (!window.MQCBundle) return;
    const section = bundleFragment(location.hash).section;
    if (section) requestAnimationFrame(() => document.getElementById(section)?.scrollIntoView());
  };
  window.addEventListener("DOMContentLoaded", scrollToOutput);
  window.addEventListener("hashchange", scrollToOutput);
}
