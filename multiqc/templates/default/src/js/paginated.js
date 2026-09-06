/* The row model is authoritative; the DOM is only the current window onto it. */
import { formatSignificant, fieldDigits } from "./precision.js";
window.addEventListener("DOMContentLoaded", () => {
  if (!window.MQCBundle) return;
  const page = window.MQCPageData;
  const models = new Map();
  const download = (name, text) => {
    const url = URL.createObjectURL(new Blob([text], { type: "text/tab-separated-values;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  for (const [id, data] of Object.entries(page.tables)) {
    const table = document.getElementById(id);
    if (!table) throw new Error(`Missing declared paginated table: ${id}`);
    const model = { data, page: 0, search: "", column: null, direction: 1, expanded: new Set() };
    models.set(id, model);
    const controls = document.createElement("div"); controls.className = "d-flex flex-wrap gap-2 align-items-center my-2";
    const search = document.createElement("input"); search.type = "search"; search.placeholder = "Search all rows";
    search.setAttribute("aria-label", "Search all table rows"); search.className = "form-control form-control-sm w-auto";
    const prev = document.createElement("button"), next = document.createElement("button"), exp = document.createElement("button");
    prev.textContent = "Previous"; next.textContent = "Next"; exp.textContent = "Download all rows";
    for (const button of [prev, next, exp]) { button.type = "button"; button.className = "btn btn-sm btn-outline-secondary"; }
    const count = document.createElement("span"); count.setAttribute("aria-live", "polite");
    controls.append(search, prev, count, next, exp); table.parentElement.before(controls);
    model.cells = (row) => row.text.map((value, i) => {
      const numeric = row.numeric[i];
      if (numeric.value == null) return value;
      const formatted = formatSignificant(numeric.value, fieldDigits(numeric.field), window.mqc_config?.decimalPoint_format);
      return formatted == null ? value : formatted + (numeric.suffix ? ` ${numeric.suffix}` : "");
    });
    model.tsv = (rows = data.rows, precise = false) => [data.headers, ...rows.map((row) => precise ? row.precise : model.cells(row))].map((cells) => cells.map((v) => String(v).replace(/[\t\r\n]/g, " ")).join("\t")).join("\n") + "\n";
    model.csv = (format) => {
      const separator = format === "tsv" ? "\t" : ",";
      return [data.headers, ...data.rows.map((row) => row.precise)].map((cells) => cells.map((value) => {
        const text = String(value);
        return /[\r\n"]/.test(text) || text.includes(separator) ? '"' + text.replace(/"/g, '""') + '"' : text;
      }).join(separator)).join("\n") + "\n";
    };
    model.settings = (row) => {
      let name = row.sample || "";
      (window.mqc_rename_f_texts || []).forEach((pattern, i) => { name = name.replace(pattern, window.mqc_rename_t_texts[i]); });
      const match = (patterns, regex, values) => patterns.some((pattern) => values.some((value) => regex ? new RegExp(pattern).test(value) : value.includes(pattern)));
      let hidden = false;
      const patterns = window.mqc_hide_f_texts || [];
      if (patterns.length) {
        const matches = match(patterns, window.mqc_hide_regex_mode, [name, row.group || ""]);
        hidden = window.mqc_hide_mode === "show" ? !matches : matches;
      }
      let highlight = null;
      (window.mqc_highlight_f_texts || []).forEach((pattern, i) => {
        if (match([pattern], window.mqc_highlight_regex_mode, [name])) highlight = window.mqc_highlight_f_cols[i];
      });
      return { name, hidden, highlight };
    };
    model.filtered = () => data.rows.filter((row) => {
      const allowed = window.dayoa_selector_allowed_ids;
      const settings = model.settings(row);
      return !settings.hidden && (!allowed || !row.sample || allowed.has(row.sample)) && (!model.search || [settings.name, ...row.text].some((value) => value.toLowerCase().includes(model.search)));
    });
    model.render = () => {
      const rows = model.filtered();
      const grouped = new Map();
      for (const row of rows) {
        const key = row.group || row.sample || row;
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(row);
      }
      const groups = [...grouped.values()];
      if (model.column !== null) groups.sort((a, b) => {
        const left = a[0].values[model.column], right = b[0].values[model.column];
        const numeric = left !== "" && right !== "" && Number.isFinite(Number(left)) && Number.isFinite(Number(right));
        return model.direction * (numeric ? Number(left) - Number(right) : String(left).localeCompare(String(right)));
      });
      const expandedRows = groups.flatMap((group) => {
        const key = group[0].group;
        return model.expanded.has(key) ? group : [group.find((r) => !r.secondary) || group[0]];
      });
      model.page = Math.min(model.page, Math.max(0, Math.ceil(expandedRows.length / 50) - 1));
      const visible = expandedRows.slice(model.page * 50, (model.page + 1) * 50);
      table.tBodies[0].innerHTML = visible.map((row) => row.html).join("");
      window.mqcApplyPrecision?.(table);
      table.querySelectorAll(".expandable-row-secondary-hidden").forEach((row) => row.classList.remove("expandable-row-secondary-hidden"));
      // Column visibility is stored in the native header, not in the windowed rows.
      const headers = [...table.tHead.rows[0].cells];
      for (const [index, row] of [...table.tBodies[0].rows].entries()) {
        const cells = [...row.cells];
        row.replaceChildren(...headers.map((header, i) => cells[i === 0 ? 0 : data.columns.indexOf(header.id.replace(/^header_/, ""))]));
        [...row.cells].forEach((cell, i) => cell.classList.toggle("column-hidden", headers[i]?.classList.contains("column-hidden")));
        const settings = model.settings(visible[index]);
        const sample = row.querySelector(".th-sample-name");
        if (sample) { sample.textContent = settings.name; sample.style.color = settings.highlight || ""; }
      }
      prev.disabled = model.page === 0; next.disabled = (model.page + 1) * 50 >= expandedRows.length;
      count.textContent = `Page ${model.page + 1} of ${Math.max(1, Math.ceil(expandedRows.length / 50))}; ${rows.length} matching rows / ${data.rows.length} total`;
      const nativeCount = document.getElementById(`${id}_numrows`); if (nativeCount) nativeCount.textContent = String(rows.length);
    };
    search.addEventListener("input", () => { model.search = search.value.toLowerCase(); model.page = 0; model.render(); });
    prev.addEventListener("click", () => { model.page--; model.render(); });
    next.addEventListener("click", () => { model.page++; model.render(); });
    exp.addEventListener("click", () => download(`${id}.tsv`, model.tsv(data.rows, true)));
    table.tHead.addEventListener("click", (event) => {
      const th = event.target.closest("th"); if (!th) return;
      const column = th.cellIndex === 0 ? 0 : data.columns.indexOf(th.id.replace(/^header_/, ""));
      model.direction = model.column === column ? -model.direction : 1; model.column = column; model.render();
    });
    table.addEventListener("click", (event) => {
      if (!event.target.closest(".expandable-row-primary") || window.getSelection().toString()) return;
      event.stopImmediatePropagation();
      const key = event.target.closest("tr").dataset.sampleGroup;
      if (model.expanded.has(key)) model.expanded.delete(key); else model.expanded.add(key);
      model.render();
    }, true);
    model.render();
  }
  window.MQCPaginatedTables = models;
  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".mqc_table_copy_btn");
    if (!button) return;
    const model = models.get(button.dataset.clipboardTarget?.replace(/^(?:table)?#/, ""));
    if (!model) return;
    event.stopImmediatePropagation(); event.preventDefault();
    try { await navigator.clipboard.writeText(model.tsv(model.filtered())); button.textContent = "Copied matching rows"; }
    catch (error) { button.textContent = "Clipboard unavailable; use Download all rows"; console.error(error); }
  }, true);
  $(document).on("dayoa_selector_filter", () => { models.forEach((model) => { model.page = 0; model.render(); }); });
  $(document).on("mqc_hidesamples mqc_renamesamples mqc_highlights", () => { models.forEach((model) => { model.page = 0; model.render(); }); });
  window.addEventListener("pagehide", () => {
    Object.keys(window.mqc_plots || {}).forEach((id) => {
      const element = document.getElementById(id); if (element && window.Plotly) Plotly.purge(element);
    });
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      models.forEach((model) => model.render());
      Object.keys(window.mqc_plots || {}).forEach((id) => { if (document.getElementById(id)) window.renderPlot(id); });
    }
  });
});
