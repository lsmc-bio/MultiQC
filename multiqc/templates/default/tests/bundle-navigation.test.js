import assert from "node:assert/strict";
import test from "node:test";
import { bundleFragment, bundleHref } from "../src/js/bundle-navigation.js";

test("group navigation preserves section, selector state and exact signed query", () => {
  const state = { modality: "sr", included: { sample: ["a&b"] } };
  const url = "https://example.test/page?X-Amz-Signature=a%2Fb%2BC#tool-section";
  const result = bundleHref(url, state);
  assert.equal(result.split("#")[0], url.split("#")[0]);
  const restored = bundleFragment(result.slice(result.indexOf("#")));
  assert.equal(restored.section, "tool-section");
  assert.deepEqual(JSON.parse(restored.state), state);
  assert.equal(bundleHref(result, state), result);
});

test("plain output anchors and selector-only navigation remain distinct", () => {
  assert.deepEqual(bundleFragment("#tool-section"), { section: "tool-section", state: null });
  assert.equal(bundleFragment(bundleHref("page.html", {}).slice(9)).section, null);
});

test("within-tab output links retain the complete selected state", () => {
  const state = { modality: "sr", included: {}, excluded: {} };
  const link = bundleHref("#output-two", state);
  assert.equal(bundleFragment(link).section, "output-two");
  assert.deepEqual(JSON.parse(bundleFragment(link).state), state);
});
