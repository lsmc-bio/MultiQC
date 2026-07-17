/* Exact, manifest-driven report display filtering for DayOA reports. */

(() => {
  "use strict";

  const manifestElement = document.getElementById("dayoa_report_selectors");
  if (!manifestElement) return;

  const manifest = JSON.parse(manifestElement.textContent);
  if (manifest.schema_version !== "dayoa-report-selectors-v2" || !Array.isArray(manifest.records)) {
    throw new Error("Invalid embedded DayOA report selector manifest");
  }

  const dimensions = {
    specimen: ["SPECIMEN_ID", "SPECIMEN_EUID"],
    sample: ["SAMPLEID", "SAMPLE_EUID"],
    library: ["ANALYSIS_UNIT_UID", "LIBRARY_EUID"],
  };
  const state = {
    modality: "all",
    selected: Object.fromEntries(Object.keys(dimensions).map((dimension) => [dimension, new Set()])),
  };
  const storageKey = `dayoa.report-selectors.${window.reportUuid || "report"}`;

  const identityKey = (record, dimension) => {
    const [idField, euidField] = dimensions[dimension];
    if (!record[idField] && !record[euidField]) return null;
    return JSON.stringify([record[idField], record[euidField]]);
  };
  const identityLabel = (key) => {
    const [id, euid] = JSON.parse(key);
    return euid ? `${id} · ${euid}` : id;
  };
  const availableIdentities = Object.fromEntries(
    Object.keys(dimensions).map((dimension) => {
      const keys = new Set(manifest.records.map((record) => identityKey(record, dimension)).filter(Boolean));
      return [dimension, [...keys].sort((left, right) => identityLabel(left).localeCompare(identityLabel(right)))];
    }),
  );

  const saveState = () => {
    const serialized = {
      modality: state.modality,
      selected: Object.fromEntries(
        Object.entries(state.selected).map(([dimension, values]) => [dimension, [...values]]),
      ),
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(serialized));
    } catch (_error) {
      // Filtering remains available for the current view without persistence.
    }
  };

  const restoreState = () => {
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem(storageKey));
    } catch (_error) {
      return;
    }
    if (!saved || !["all", "sr", "lr", "hybrid"].includes(saved.modality)) return;
    state.modality = saved.modality;
    Object.keys(dimensions).forEach((dimension) => {
      const allowed = new Set(availableIdentities[dimension]);
      const selected = Array.isArray(saved.selected?.[dimension]) ? saved.selected[dimension] : [];
      state.selected[dimension] = new Set(selected.filter((key) => allowed.has(key)));
    });
  };

  const recordMatches = (record) => {
    if (state.modality !== "all" && record.modality !== state.modality && record.modality !== "global") return false;
    return Object.keys(dimensions).every((dimension) => {
      if (state.selected[dimension].size === 0) return true;
      const key = identityKey(record, dimension);
      return key !== null && state.selected[dimension].has(key);
    });
  };
  const filtersAreActive = () =>
    state.modality !== "all" || Object.values(state.selected).some((selected) => selected.size > 0);

  const updateTables = () => {
    document.querySelectorAll(".mqc_per_sample_table tbody tr").forEach((row) => {
      const sample = row.querySelector(".th-sample-name")?.dataset.originalSn;
      const hidden = window.dayoa_selector_allowed_ids !== null && !window.dayoa_selector_allowed_ids.has(sample);
      row.classList.toggle("dayoa-selector-hidden", hidden);
    });
    document.querySelectorAll(".mqc_table_numrows").forEach((counter) => {
      const tableId = counter.id.replace("_numrows", "");
      const selector = `#${CSS.escape(tableId)} tbody tr:not(.sample-hidden):not(.dayoa-selector-hidden)`;
      counter.textContent = String(document.querySelectorAll(selector).length);
    });
  };

  const applyFilters = () => {
    window.dayoa_selector_allowed_ids = filtersAreActive()
      ? new Set(manifest.records.filter(recordMatches).map((record) => record.MultiQCAnalysisID))
      : null;
    updateTables();
    $(document).trigger("dayoa_selector_filter");
    const visible = window.dayoa_selector_allowed_ids === null ? manifest.records.length : window.dayoa_selector_allowed_ids.size;
    const status = document.getElementById("dayoa-selector-status");
    if (status) status.textContent = `Showing ${visible} of ${manifest.records.length} report records`;
    saveState();
  };

  const updateControls = () => {
    document.querySelectorAll(".dayoa-modality-button").forEach((button) => {
      const active = button.dataset.modality === state.modality;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    document.querySelectorAll(".dayoa-identity-chip").forEach((button) => {
      const selected = state.selected[button.dataset.dimension].has(button.dataset.identityKey);
      button.classList.toggle("active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  };

  const renderIdentityControls = () => {
    Object.keys(dimensions).forEach((dimension) => {
      const control = document.querySelector(`[data-identity-dimension="${dimension}"]`);
      const list = control.querySelector(".dayoa-identity-chip-list");
      availableIdentities[dimension].forEach((key) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "dayoa-identity-chip";
        button.dataset.dimension = dimension;
        button.dataset.identityKey = key;
        button.textContent = identityLabel(key);
        button.setAttribute("aria-pressed", "false");
        button.addEventListener("click", () => {
          if (state.selected[dimension].has(key)) state.selected[dimension].delete(key);
          else state.selected[dimension].add(key);
          updateControls();
          applyFilters();
        });
        list.appendChild(button);
      });
      control.querySelector(".dayoa-identity-search").addEventListener("input", (event) => {
        const query = event.target.value.trim().toLocaleLowerCase();
        list.querySelectorAll(".dayoa-identity-chip").forEach((button) => {
          button.hidden = query !== "" && !button.textContent.toLocaleLowerCase().includes(query);
        });
      });
    });
  };

  window.dayoaWithSelectorsSuspended = (callback) => {
    const selected = window.dayoa_selector_allowed_ids;
    window.dayoa_selector_allowed_ids = null;
    try {
      return callback();
    } finally {
      window.dayoa_selector_allowed_ids = selected;
    }
  };

  window.dayoa_selector_allowed_ids = null;
  window.addEventListener("DOMContentLoaded", () => {
    renderIdentityControls();
    restoreState();
    updateControls();
    document.querySelectorAll(".dayoa-modality-button").forEach((button) => {
      button.addEventListener("click", () => {
        state.modality = button.dataset.modality;
        updateControls();
        applyFilters();
      });
    });
    document.getElementById("dayoa-selector-clear").addEventListener("click", () => {
      state.modality = "all";
      Object.values(state.selected).forEach((selected) => selected.clear());
      document.querySelectorAll(".dayoa-identity-search").forEach((input) => {
        input.value = "";
        input.dispatchEvent(new Event("input"));
      });
      updateControls();
      applyFilters();
    });
    applyFilters();
  });
})();
