import assert from "node:assert/strict";
import test from "node:test";

import {
  createDayoaSelectorState,
  cycleDayoaSelectorValue,
  dayoaFiltersAreActive,
  dayoaIdentityKey,
  dayoaRecordMatches,
  dayoaSelectorIdentityKeys,
  dayoaSelectorValueState,
  validateDayoaSelectorManifest,
  validateDayoaPlotGroupingCoverage,
  validateDayoaPlotGroupings,
} from "../src/js/dayoa-selectors.js";

const records = [
  {
    MultiQCAnalysisID: "spec-a_sample-a_lib-a_sr",
    modality: "sr",
    SPECIMEN_ID: "spec-a",
    SPECIMEN_EUID: "spec-euid-a",
    SAMPLEID: "sample-a",
    SAMPLE_EUID: "sample-euid-a",
    ANALYSIS_UNIT_UID: "lib-a",
    ANALYSIS_UNIT_EUID: "analysis-unit-euid-a",
    LIBRARY_EUID: "library-euid-a",
    selector_eligible: true,
  },
  {
    MultiQCAnalysisID: "spec-a_sample-b_lib-b_lr",
    modality: "lr",
    SPECIMEN_ID: "spec-a",
    SPECIMEN_EUID: "spec-euid-a",
    SAMPLEID: "sample-b",
    SAMPLE_EUID: "sample-euid-b",
    ANALYSIS_UNIT_UID: "lib-b",
    ANALYSIS_UNIT_EUID: "analysis-unit-euid-b",
    LIBRARY_EUID: "library-euid-b",
    selector_eligible: true,
  },
  {
    MultiQCAnalysisID: "spec-c_sample-c_lib-c_hybrid",
    modality: "hybrid",
    SPECIMEN_ID: "spec-c",
    SPECIMEN_EUID: "spec-euid-c",
    SAMPLEID: "sample-c",
    SAMPLE_EUID: "sample-euid-c",
    ANALYSIS_UNIT_UID: "lib-c",
    ANALYSIS_UNIT_EUID: "analysis-unit-euid-c",
    LIBRARY_EUID: "library-euid-c",
    selector_eligible: true,
  },
  {
    MultiQCAnalysisID: "spec-d_sample-d_lib-d_rsr",
    modality: "rsr",
    SPECIMEN_ID: "spec-d",
    SPECIMEN_EUID: "spec-euid-d",
    SAMPLEID: "sample-d",
    SAMPLE_EUID: "sample-euid-d",
    ANALYSIS_UNIT_UID: "lib-d",
    ANALYSIS_UNIT_EUID: "analysis-unit-euid-d",
    LIBRARY_EUID: "library-euid-d",
    selector_eligible: true,
  },
  {
    MultiQCAnalysisID: "workflow_global",
    modality: "global",
    SPECIMEN_ID: null,
    SPECIMEN_EUID: null,
    SAMPLEID: null,
    SAMPLE_EUID: null,
    ANALYSIS_UNIT_UID: null,
    ANALYSIS_UNIT_EUID: null,
    LIBRARY_EUID: null,
    selector_eligible: false,
  },
];

const selectorManifest = () => ({
  schema_version: "dayoa-report-selectors-v3",
  records,
  plot_groupings: {},
  source_staging_manifest: "manifest.tsv",
  source_row_count: records.length,
  record_count: records.length,
  selector_record_count: records.length - 1,
  selector_records: records.slice(0, -1),
});

test("v3 manifest validation accepts an exact selector subset", () => {
  const manifest = selectorManifest();

  assert.equal(validateDayoaSelectorManifest(manifest), manifest);
});

test("manifest validation rejects v2 and count or selector subset drift", () => {
  const old = selectorManifest();
  old.schema_version = "dayoa-report-selectors-v2";
  assert.throws(() => validateDayoaSelectorManifest(old), /must use dayoa-report-selectors-v3/);

  const countMismatch = selectorManifest();
  countMismatch.record_count -= 1;
  assert.throws(() => validateDayoaSelectorManifest(countMismatch), /record_count does not match records/);

  const subsetMismatch = selectorManifest();
  subsetMismatch.selector_records = [records[4], ...records.slice(1, -1)];
  assert.throws(() => validateDayoaSelectorManifest(subsetMismatch), /in-order selector-eligible subset/);
});

test("non-selector records do not create analysis-unit selector identities", () => {
  const nonSelectorWithIdentity = {
    ...records[4],
    ANALYSIS_UNIT_UID: "must-not-be-a-control",
    ANALYSIS_UNIT_EUID: "must-not-be-a-control-euid",
  };

  assert.deepEqual(
    dayoaSelectorIdentityKeys([...records.slice(0, -1), nonSelectorWithIdentity], "analysis_unit"),
    records.slice(0, -1).map((record) => dayoaIdentityKey(record, "analysis_unit")),
  );
});

test("selector values cycle neutral to include to exclude to neutral", () => {
  const state = createDayoaSelectorState();
  const key = dayoaIdentityKey(records[0], "analysis_unit");

  assert.equal(dayoaSelectorValueState(state, "analysis_unit", key), "neutral");
  assert.equal(cycleDayoaSelectorValue(state, "analysis_unit", key), "include");
  assert.equal(cycleDayoaSelectorValue(state, "analysis_unit", key), "exclude");
  assert.equal(cycleDayoaSelectorValue(state, "analysis_unit", key), "neutral");
  assert.equal(dayoaFiltersAreActive(state), false);
});

test("includes are OR within a dimension and AND across dimensions", () => {
  const state = createDayoaSelectorState();
  state.included.specimen.add(dayoaIdentityKey(records[0], "specimen"));
  state.included.analysis_unit.add(dayoaIdentityKey(records[0], "analysis_unit"));
  state.included.analysis_unit.add(dayoaIdentityKey(records[1], "analysis_unit"));

  assert.equal(dayoaRecordMatches(records[0], state), true);
  assert.equal(dayoaRecordMatches(records[1], state), true);
  assert.equal(dayoaRecordMatches(records[2], state), false);
});

test("exclusions form a negative set and override matching includes", () => {
  const state = createDayoaSelectorState();
  state.included.specimen.add(dayoaIdentityKey(records[0], "specimen"));
  state.excluded.analysis_unit.add(dayoaIdentityKey(records[1], "analysis_unit"));

  assert.equal(dayoaRecordMatches(records[0], state), true);
  assert.equal(dayoaRecordMatches(records[1], state), false);
  assert.equal(dayoaRecordMatches(records[2], state), false);
});

test("modality and identity filters compose without changing identifiers", () => {
  const state = createDayoaSelectorState();
  state.modality = "lr";
  state.included.sample.add(dayoaIdentityKey(records[1], "sample"));
  const original = structuredClone(records);

  assert.deepEqual(records.filter((record) => dayoaRecordMatches(record, state)), [records[1], records[4]]);
  assert.deepEqual(records, original);
});

test("RSR filtering preserves global records and composes with identities", () => {
  const state = createDayoaSelectorState();
  state.modality = "rsr";
  state.included.sample.add(dayoaIdentityKey(records[3], "sample"));

  assert.deepEqual(
    records.filter((record) => dayoaRecordMatches(record, state)),
    [records[3], records[4]],
  );
  assert.equal(dayoaFiltersAreActive(state), true);
});

const validGrouping = {
  "sample-aware-plot": [
    {
      id: "modality",
      label: "Modality",
      groups: [
        { value: "short-read/arbitrary", label: "Short read", members: [records[0].MultiQCAnalysisID] },
        { value: "long-read arbitrary", label: "Long read", members: [records[1].MultiQCAnalysisID] },
      ],
    },
  ],
};

test("plot grouping validation preserves explicit producer values and order", () => {
  const original = structuredClone(validGrouping);
  const validated = validateDayoaPlotGroupings(
    validGrouping,
    records.map((record) => record.MultiQCAnalysisID),
  );

  assert.equal(validated, validGrouping);
  assert.deepEqual(validated, original);
  assert.deepEqual(
    validated["sample-aware-plot"][0].groups.map((group) => group.value),
    ["short-read/arbitrary", "long-read arbitrary"],
  );
});

test("plot grouping validation rejects unknown and duplicate members", () => {
  const known = records.map((record) => record.MultiQCAnalysisID);
  const unknown = structuredClone(validGrouping);
  unknown["sample-aware-plot"][0].groups[0].members = ["not-in-selector-manifest"];
  assert.throws(() => validateDayoaPlotGroupings(unknown, known), /references unknown member/);

  const duplicate = structuredClone(validGrouping);
  duplicate["sample-aware-plot"][0].groups[1].members = [records[0].MultiQCAnalysisID];
  assert.throws(() => validateDayoaPlotGroupings(duplicate, known), /repeats member/);
});

test("plot grouping coverage must exactly equal the plotted analysis IDs", () => {
  const dimension = validGrouping["sample-aware-plot"][0];
  assert.equal(
    validateDayoaPlotGroupingCoverage("sample-aware-plot", dimension, [
      records[0].MultiQCAnalysisID,
      records[1].MultiQCAnalysisID,
    ]),
    undefined,
  );
  assert.throws(
    () =>
      validateDayoaPlotGroupingCoverage("sample-aware-plot", dimension, [
        records[0].MultiQCAnalysisID,
        records[2].MultiQCAnalysisID,
      ]),
    /missing: .*lib-c_hybrid.*unknown: .*lib-b_lr/,
  );
});
