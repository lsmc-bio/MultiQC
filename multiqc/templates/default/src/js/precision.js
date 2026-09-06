/* Display-only precision. Numeric provenance and science exports are immutable. */
export function formatSignificant(value, digits, decimalPoint = ".") {
  if (digits == null) return null;
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  // Counts are exact, not approximate measurements. Never round an integer
  // merely because the report requests significant digits for fractions.
  // Preserve the original string before any unsafe IEEE-754 conversion.
  if (/^-?\d+$/.test(String(value))) return String(value);
  if (Number.isSafeInteger(number)) return String(number);
  const result = Number(number.toPrecision(digits)).toString();
  return decimalPoint === "." ? result : result.replace(".", decimalPoint);
}

export function fieldDigits(key) {
  const display = window.MQCPresentation?.display;
  if (!display) return null;
  return Object.prototype.hasOwnProperty.call(display.fields, key) ? display.fields[key] : display.significant_digits;
}

if (typeof window !== "undefined") {
window.mqcApplyPrecision = (root = document) => {
  root.querySelectorAll("td[data-numeric-value]").forEach((cell) => {
    const target = cell.querySelector(".mqc-numeric-token");
    if (!target) return;
    if (target.dataset.nativeHtml === undefined) target.dataset.nativeHtml = target.innerHTML;
    const digits = fieldDigits(cell.dataset.fieldId);
    const formatted = formatSignificant(cell.dataset.numericValue, digits, window.mqc_config?.decimalPoint_format);
    if (formatted == null) { target.innerHTML = target.dataset.nativeHtml; return; }
    target.textContent = formatted;
    cell.title = `Underlying value: ${cell.dataset.rawValue}; display-unit value: ${cell.dataset.numericValue}; field: ${cell.dataset.fieldId}`;
  });
};
window.addEventListener("DOMContentLoaded", () => window.mqcApplyPrecision());
}
