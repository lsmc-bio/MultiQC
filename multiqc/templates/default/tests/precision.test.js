import assert from "node:assert/strict";
import test from "node:test";
import { formatSignificant } from "../src/js/precision.js";

test("significant digits retain small nonzero values and configurable resolution", () => {
  assert.equal(formatSignificant("0.000000123456789", 6), "1.23457e-7");
  assert.equal(formatSignificant("0.123456789", 6), "0.123457");
  assert.equal(formatSignificant("0.123456789", 8), "0.12345679");
  assert.equal(formatSignificant("0.123456789", null), null);
  assert.equal(formatSignificant("9007199254740993", 6), "9007199254740993");
  assert.equal(formatSignificant("0.123456789", 6, ","), "0,123457");
});
