/* Exact, manifest-driven report display filtering for DayOA reports. */

export const dayoaSelectorDimensions = {
  specimen: ["SPECIMEN_ID", "SPECIMEN_EUID"],
  sample: ["SAMPLEID", "SAMPLE_EUID"],
  analysis_unit: ["ANALYSIS_UNIT_UID", "ANALYSIS_UNIT_EUID"],
};

const dayoaSelectorTopLevelFields = [
  "plot_groupings",
  "record_count",
  "records",
  "schema_version",
  "selector_record_count",
  "selector_records",
  "source_row_count",
  "source_staging_manifest",
];

export const createDayoaSelectorState = () => ({
  modality: "all",
  included: Object.fromEntries(Object.keys(dayoaSelectorDimensions).map((dimension) => [dimension, new Set()])),
  excluded: Object.fromEntries(Object.keys(dayoaSelectorDimensions).map((dimension) => [dimension, new Set()])),
});

export const dayoaIdentityKey = (record, dimension) => {
  const [idField, euidField] = dayoaSelectorDimensions[dimension];
  if (!record[idField] && !record[euidField]) return null;
  return JSON.stringify([record[idField], record[euidField]]);
};

export const dayoaSelectorIdentityKeys = (records, dimension) =>
  [
    ...new Set(
      records
        .filter((record) => record.selector_eligible === true)
        .map((record) => dayoaIdentityKey(record, dimension))
        .filter(Boolean),
    ),
  ];

export const validateDayoaSelectorManifest = (manifest) => {
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new Error("DayOA report selector manifest must be an object");
  }
  const actualFields = Object.keys(manifest).sort();
  if (JSON.stringify(actualFields) !== JSON.stringify(dayoaSelectorTopLevelFields)) {
    throw new Error("DayOA report selector manifest must contain the exact v3 top-level fields");
  }
  if (manifest.schema_version !== "dayoa-report-selectors-v3") {
    throw new Error("DayOA report selector manifest must use dayoa-report-selectors-v3");
  }
  if (!Array.isArray(manifest.records) || manifest.records.length === 0) {
    throw new Error("DayOA report selector manifest records must be a non-empty array");
  }
  if (!Array.isArray(manifest.selector_records)) {
    throw new Error("DayOA report selector manifest selector_records must be an array");
  }
  if (!Number.isInteger(manifest.record_count) || manifest.record_count !== manifest.records.length) {
    throw new Error("DayOA report selector manifest record_count does not match records");
  }
  if (
    !Number.isInteger(manifest.selector_record_count) ||
    manifest.selector_record_count !== manifest.selector_records.length
  ) {
    throw new Error("DayOA report selector manifest selector_record_count does not match selector_records");
  }
  if (!Number.isInteger(manifest.source_row_count) || manifest.source_row_count < manifest.record_count) {
    throw new Error("DayOA report selector manifest source_row_count is invalid");
  }
  if (typeof manifest.source_staging_manifest !== "string" || !manifest.source_staging_manifest) {
    throw new Error("DayOA report selector manifest source_staging_manifest is invalid");
  }
  if (!manifest.plot_groupings || typeof manifest.plot_groupings !== "object" || Array.isArray(manifest.plot_groupings)) {
    throw new Error("DayOA report selector manifest plot_groupings must be an object");
  }

  const knownAnalysisIds = manifest.records.map((record) => record.MultiQCAnalysisID);
  if (knownAnalysisIds.some((analysisId) => typeof analysisId !== "string" || !analysisId)) {
    throw new Error("DayOA report selector manifest has a blank or invalid MultiQCAnalysisID");
  }
  if (new Set(knownAnalysisIds).size !== knownAnalysisIds.length) {
    throw new Error("DayOA report selector manifest repeats a MultiQCAnalysisID");
  }
  if (manifest.records.some((record) => typeof record.selector_eligible !== "boolean")) {
    throw new Error("DayOA report selector manifest records must declare boolean selector_eligible values");
  }
  const expectedSelectorRecords = manifest.records.filter((record) => record.selector_eligible);
  if (
    expectedSelectorRecords.length !== manifest.selector_records.length ||
    expectedSelectorRecords.some(
      (record, index) => JSON.stringify(record) !== JSON.stringify(manifest.selector_records[index]),
    )
  ) {
    throw new Error(
      "DayOA report selector manifest selector_records must equal the in-order selector-eligible subset of records",
    );
  }
  return manifest;
};

export const dayoaSelectorValueState = (state, dimension, key) => {
  if (state.included[dimension].has(key)) return "include";
  if (state.excluded[dimension].has(key)) return "exclude";
  return "neutral";
};

export const cycleDayoaSelectorValue = (state, dimension, key) => {
  const current = dayoaSelectorValueState(state, dimension, key);
  state.included[dimension].delete(key);
  state.excluded[dimension].delete(key);
  if (current === "neutral") state.included[dimension].add(key);
  if (current === "include") state.excluded[dimension].add(key);
  return dayoaSelectorValueState(state, dimension, key);
};

export const dayoaRecordMatches = (record, state) => {
  if (record.modality === "global") return true;
  if (state.modality !== "all" && record.modality !== state.modality) return false;
  return Object.keys(dayoaSelectorDimensions).every((dimension) => {
    const key = dayoaIdentityKey(record, dimension);
    if (state.excluded[dimension].has(key)) return false;
    return state.included[dimension].size === 0 || (key !== null && state.included[dimension].has(key));
  });
};

export const dayoaFiltersAreActive = (state) =>
  state.modality !== "all" ||
  Object.values(state.included).some((values) => values.size > 0) ||
  Object.values(state.excluded).some((values) => values.size > 0);

export const validateDayoaPlotGroupings = (plotGroupings, knownAnalysisIds) => {
  if (plotGroupings === undefined) return {};
  if (!plotGroupings || typeof plotGroupings !== "object" || Array.isArray(plotGroupings)) {
    throw new Error("DayOA plot_groupings must be an object keyed by plot ID");
  }
  const known = new Set(knownAnalysisIds);
  Object.entries(plotGroupings).forEach(([plotId, dimensions]) => {
    if (!plotId || !Array.isArray(dimensions) || dimensions.length === 0) {
      throw new Error(`DayOA plot grouping ${plotId || "<blank>"} must declare at least one dimension`);
    }
    const dimensionIds = new Set();
    dimensions.forEach((dimension) => {
      if (!dimension || typeof dimension.id !== "string" || !dimension.id || typeof dimension.label !== "string" || !dimension.label) {
        throw new Error(`DayOA plot grouping ${plotId} has an invalid dimension identity`);
      }
      if (dimensionIds.has(dimension.id)) {
        throw new Error(`DayOA plot grouping ${plotId} repeats dimension ${dimension.id}`);
      }
      dimensionIds.add(dimension.id);
      if (!Array.isArray(dimension.groups) || dimension.groups.length === 0) {
        throw new Error(`DayOA plot grouping ${plotId}/${dimension.id} must declare at least one group`);
      }
      const values = new Set();
      const members = new Set();
      dimension.groups.forEach((group) => {
        if (!group || typeof group.value !== "string" || !group.value || typeof group.label !== "string" || !group.label) {
          throw new Error(`DayOA plot grouping ${plotId}/${dimension.id} has an invalid group identity`);
        }
        if (values.has(group.value)) {
          throw new Error(`DayOA plot grouping ${plotId}/${dimension.id} repeats group ${group.value}`);
        }
        values.add(group.value);
        if (!Array.isArray(group.members) || group.members.length === 0) {
          throw new Error(`DayOA plot grouping ${plotId}/${dimension.id}/${group.value} has no members`);
        }
        group.members.forEach((member) => {
          if (typeof member !== "string" || !known.has(member)) {
            throw new Error(`DayOA plot grouping ${plotId}/${dimension.id} references unknown member ${member}`);
          }
          if (members.has(member)) {
            throw new Error(`DayOA plot grouping ${plotId}/${dimension.id} repeats member ${member}`);
          }
          members.add(member);
        });
      });
    });
  });
  return plotGroupings;
};

export const validateDayoaPlotGroupingCoverage = (plotId, dimension, plottedAnalysisIds) => {
  const plotted = new Set(plottedAnalysisIds);
  const declared = new Set(dimension.groups.flatMap((group) => group.members));
  const missing = [...plotted].filter((member) => !declared.has(member)).sort();
  const unknown = [...declared].filter((member) => !plotted.has(member)).sort();
  if (missing.length || unknown.length) {
    throw new Error(
      `DayOA plot grouping ${plotId}/${dimension.id} does not exactly cover plotted analysis IDs; missing: ${missing.join(", ") || "none"}; unknown: ${unknown.join(", ") || "none"}`,
    );
  }
};

(() => {
  "use strict";

  if (typeof document === "undefined") return;
  const manifestElement = document.getElementById("dayoa_report_selectors");
  if (!manifestElement && !window.MQCBundle?.identities.analysis_unit.length) return;

  const manifest = window.MQCBundle
    ? { ...window.MQCPageData.selectors, selector_records: window.MQCPageData.selectors.records.filter((r) => r.selector_eligible) }
    : validateDayoaSelectorManifest(JSON.parse(manifestElement.textContent));
  if (window.MQCBundle) Object.values(manifest.plot_groupings).forEach((dimensions) => dimensions.forEach((dimension) => dimension.groups.forEach((group) => {
    group.members = manifest.memberships[group.members_ref];
    delete group.members_ref;
  })));
  const knownAnalysisIds = manifest.records.map((record) => record.MultiQCAnalysisID);
  const plotGroupings = validateDayoaPlotGroupings(manifest.plot_groupings, knownAnalysisIds);

  const state = createDayoaSelectorState();
  const storageKey = `dayoa.report-selectors.v3.${window.reportUuid || "report"}`;

  const identityLabel = (key) => {
    const [id, euid] = JSON.parse(key);
    return euid ? `${id} · ${euid}` : id;
  };
  const availableIdentities = Object.fromEntries(
    Object.keys(dayoaSelectorDimensions).map((dimension) => {
      const keys = window.MQCBundle ? window.MQCBundle.identities[dimension] : dayoaSelectorIdentityKeys(manifest.selector_records, dimension);
      return [dimension, keys.sort((left, right) => identityLabel(left).localeCompare(identityLabel(right)))];
    }),
  );

  const saveState = () => {
    const serialized = {
      schema_version: "dayoa-report-selector-state-v3",
      modality: state.modality,
      included: Object.fromEntries(
        Object.entries(state.included).map(([dimension, values]) => [dimension, [...values]]),
      ),
      excluded: Object.fromEntries(
        Object.entries(state.excluded).map(([dimension, values]) => [dimension, [...values]]),
      ),
    };
    if (window.MQCBundle) {
      window.MQCBundle.state = serialized;
      document.querySelectorAll("a[data-bundle-nav]").forEach((a) => {
        const original = a.dataset.bundleHref || a.getAttribute("href");
        a.dataset.bundleHref = original;
        a.href = original.split("#")[0] + "#mqc-state=" + encodeURIComponent(JSON.stringify(serialized));
      });
      history.replaceState(null, "", location.pathname + location.search + "#mqc-state=" + encodeURIComponent(JSON.stringify(serialized)));
    }
    try {
      localStorage.setItem(storageKey, JSON.stringify(serialized));
    } catch (_error) {
      // Filtering remains available for the current view without persistence.
    }
  };

  const restoreState = () => {
    let saved = null;
    try {
      const fragment = window.MQCBundle && location.hash.startsWith("#mqc-state=") ? decodeURIComponent(location.hash.slice(11)) : null;
      saved = JSON.parse(fragment || localStorage.getItem(storageKey));
    } catch (_error) {
      return;
    }
    if (
      !saved ||
      saved.schema_version !== "dayoa-report-selector-state-v3" ||
      !["all", "sr", "rsr", "lr", "hybrid"].includes(saved.modality)
    )
      return;
    state.modality = saved.modality;
    Object.keys(dayoaSelectorDimensions).forEach((dimension) => {
      const allowed = new Set(availableIdentities[dimension]);
      const included = Array.isArray(saved.included?.[dimension]) ? saved.included[dimension] : [];
      const excluded = Array.isArray(saved.excluded?.[dimension]) ? saved.excluded[dimension] : [];
      state.included[dimension] = new Set(included.filter((key) => allowed.has(key)));
      state.excluded[dimension] = new Set(excluded.filter((key) => allowed.has(key)));
      state.included[dimension].forEach((key) => state.excluded[dimension].delete(key));
    });
  };

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
    window.dayoa_selector_allowed_ids = dayoaFiltersAreActive(state)
      ? new Set(manifest.records.filter((record) => dayoaRecordMatches(record, state)).map((record) => record.MultiQCAnalysisID))
      : null;
    updateTables();
    $(document).trigger("dayoa_selector_filter");
    const visible = window.dayoa_selector_allowed_ids === null ? manifest.records.length : window.dayoa_selector_allowed_ids.size;
    const status = document.getElementById("dayoa-selector-status");
    const includedCount = Object.values(state.included).reduce((total, values) => total + values.size, 0);
    const excludedCount = Object.values(state.excluded).reduce((total, values) => total + values.size, 0);
    if (status)
      status.textContent = window.MQCBundle?.is_index
        ? `Selections apply across all sections. ${includedCount} included, ${excludedCount} excluded.`
        : `Showing ${visible} of ${manifest.records.length} section records. ${includedCount} included, ${excludedCount} excluded.`;
    saveState();
  };

  const updateControls = () => {
    document.querySelectorAll(".dayoa-modality-button").forEach((button) => {
      const active = button.dataset.modality === state.modality;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    document.querySelectorAll(".dayoa-identity-chip").forEach((button) => {
      const selectorState = dayoaSelectorValueState(state, button.dataset.dimension, button.dataset.identityKey);
      const label = button.dataset.identityLabel;
      button.dataset.selectorState = selectorState;
      button.classList.toggle("active", selectorState === "include");
      button.classList.toggle("excluded", selectorState === "exclude");
      button.setAttribute("aria-pressed", selectorState === "exclude" ? "mixed" : String(selectorState === "include"));
      button.setAttribute("aria-label", `${label}: ${selectorState === "neutral" ? "not filtering" : `${selectorState}d`}`);
      button.title =
        selectorState === "neutral"
          ? `Include ${label}`
          : selectorState === "include"
            ? `Included. Click to exclude ${label}`
            : `Excluded. Click to clear ${label}`;
    });
  };

  const renderIdentityControls = () => {
    Object.keys(dayoaSelectorDimensions).forEach((dimension) => {
      const control = document.querySelector(`[data-identity-dimension="${dimension}"]`);
      const list = control.querySelector(".dayoa-identity-chip-list");
      availableIdentities[dimension].forEach((key) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "dayoa-identity-chip";
        button.dataset.dimension = dimension;
        button.dataset.identityKey = key;
        button.dataset.identityLabel = identityLabel(key);
        button.dataset.selectorState = "neutral";
        button.textContent = button.dataset.identityLabel;
        button.setAttribute("aria-pressed", "false");
        button.addEventListener("click", () => {
          cycleDayoaSelectorValue(state, dimension, key);
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

  const plotGroupingState = {};
  window.dayoa_plot_grouping_capabilities = {};
  window.dayoaPlotGroupingFor = (plotId, analysisId) => {
    const dimensionId = plotGroupingState[plotId];
    if (!dimensionId) return null;
    const dimension = plotGroupings[plotId].find((candidate) => candidate.id === dimensionId);
    if (!dimension) return null;
    const groupIndex = dimension.groups.findIndex((candidate) => candidate.members.includes(analysisId));
    const group = dimension.groups[groupIndex];
    if (!group) throw new Error(`DayOA plot grouping ${plotId}/${dimensionId} has no group for ${analysisId}`);
    return { ...group, dayoa_group_order: groupIndex };
  };

  const plotSampleIds = (plot) => {
    const ids = [];
    plot.datasets.forEach((dataset) => {
      const series = plot.plotType === "scatter plot" ? dataset.points : dataset.lines;
      series.forEach((item) => {
        const analysisId = item.originalName ?? item.name;
        if (!ids.includes(analysisId)) ids.push(analysisId);
      });
    });
    return ids;
  };

  const groupingStorageKey = (plotId) =>
    `dayoa.plot-grouping.v1.${window.reportUuid || "report"}.${plotId}`;

  const restorePlotGrouping = (plotId, dimensions) => {
    try {
      const saved = localStorage.getItem(groupingStorageKey(plotId));
      return dimensions.some((dimension) => dimension.id === saved) ? saved : null;
    } catch (_error) {
      return null;
    }
  };

  const savePlotGrouping = (plotId, dimensionId) => {
    try {
      if (dimensionId) localStorage.setItem(groupingStorageKey(plotId), dimensionId);
      else localStorage.removeItem(groupingStorageKey(plotId));
    } catch (_error) {
      // Grouping remains available for the current view without persistence.
    }
  };

  const initializePlotGroupingControls = () => {
    Object.entries(plotGroupings).forEach(([plotId, dimensions]) => {
      const plot = window.mqc_plots[plotId];
      if (!plot) throw new Error(`DayOA plot grouping references missing plot ${plotId}`);
      const supported = ["scatter plot", "x/y line"].includes(plot.plotType);
      window.dayoa_plot_grouping_capabilities[plotId] = {
        supported,
        plot_type: plot.plotType,
        reason: supported ? "sample-aware Plotly plot" : "unsupported plot type",
      };
      const plotElement = document.getElementById(plotId);
      if (plotElement) plotElement.dataset.dayoaGroupingCapability = supported ? "supported" : "unsupported";
      if (!supported) return;

      const plottedIds = plotSampleIds(plot);
      dimensions.forEach((dimension) => validateDayoaPlotGroupingCoverage(plotId, dimension, plottedIds));
      plotGroupingState[plotId] = restorePlotGrouping(plotId, dimensions);

      const control = document.createElement("div");
      control.className = "dayoa-plot-grouping-control d-print-none";
      const label = document.createElement("label");
      const selectId = `dayoa-plot-grouping-${plotId}`;
      label.htmlFor = selectId;
      label.textContent = "Group by";
      const select = document.createElement("select");
      select.id = selectId;
      select.className = "form-select form-select-sm";
      select.setAttribute("aria-label", `Group ${plotId} visualization by`);
      select.appendChild(new Option("None", ""));
      dimensions.forEach((dimension) => select.appendChild(new Option(dimension.label, dimension.id)));
      select.value = plotGroupingState[plotId] || "";
      select.addEventListener("change", () => {
        plotGroupingState[plotId] = select.value || null;
        savePlotGrouping(plotId, plotGroupingState[plotId]);
        if (plot.rendered) window.renderPlot(plotId);
      });
      control.append(label, select);
      const wrapper = plotElement?.closest(".hc-plot-wrapper") || plotElement;
      wrapper?.parentNode?.insertBefore(control, wrapper);
    });
  };

  if (Object.keys(plotGroupings).length > 0) {
    window.callAfterDecompressed.push(initializePlotGroupingControls);
  }

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
      Object.values(state.included).forEach((included) => included.clear());
      Object.values(state.excluded).forEach((excluded) => excluded.clear());
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
