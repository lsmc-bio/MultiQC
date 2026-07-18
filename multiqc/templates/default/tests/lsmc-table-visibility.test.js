import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const originalCss = readFileSync(new URL("../src/scss/custom.scss", import.meta.url), "utf8");
const lsmcCss = readFileSync(new URL("../src/scss/_lsmc.scss", import.meta.url), "utf8");

test("the untouched original theme keeps the upstream table stacking contract", () => {
  assert.match(originalCss, /\.wrapper\s*\{[\s\S]*?z-index:\s*-10;/);
  assert.match(originalCss, /tbody tr td \.wrapper \.val\s*\{[\s\S]*?z-index:\s*-1;/);
  assert.match(originalCss, /\.bar\s*\{[\s\S]*?z-index:\s*-1;/);
});

test("all five branded themes place table values above opaque data bars", () => {
  assert.match(lsmcCss, /html\[data-theme\]:not\(\[data-theme="original"\]\)\s*\{/);
  assert.match(lsmcCss, /\.mqc_table \.wrapper\s*\{\s*z-index:\s*0;/);
  assert.match(lsmcCss, /\.mqc_table tbody tr td \.wrapper \.val\s*\{[\s\S]*?z-index:\s*1;/);
  assert.match(lsmcCss, /\.mqc_table \.bar\s*\{\s*z-index:\s*0;/);
  for (const theme of ["lsmc", "dark", "light", "nosee", "tacky"]) {
    assert.match(lsmcCss, new RegExp(`html\\[data-theme="${theme}"\\]`));
  }
});
