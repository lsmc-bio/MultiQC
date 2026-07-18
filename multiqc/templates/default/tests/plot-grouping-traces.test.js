import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

globalThis.window = {
  dayoaPlotGroupingFor: (_plotId, analysisId) => ({
    value: analysisId.startsWith("sr-") ? "sr/arbitrary" : "lr arbitrary",
    label: analysisId.startsWith("sr-") ? "Short read" : "Long read",
    dayoa_group_order: analysisId.startsWith("sr-") ? 0 : 1,
  }),
};
globalThis.Plot = class {};
globalThis.updateObject = (target, source) => Object.assign(target, source);
globalThis.applyToolboxSettings = (samples) =>
  samples.map((name) => ({ name, pseudonym: null, highlight: null, hidden: false }));

for (const filename of ["scatter.js", "line.js"]) {
  const source = readFileSync(new URL(`../src/js/plots/${filename}`, import.meta.url), "utf8");
  vm.runInThisContext(source, { filename });
}

test("scatter traces use explicit grouping while exports retain original identifiers", () => {
  const plot = Object.create(window.ScatterPlot.prototype);
  plot.anchor = "mixed-scatter";
  plot.activeDatasetIdx = 0;
  plot.pconfig = {};
  plot.datasets = [
    {
      points: [
        { name: "sr-one", x: 1, y: 2 },
        { name: "sr-two", x: 2, y: 3 },
        { name: "lr-one", x: 3, y: 4 },
      ],
      trace_params: { marker: { size: 5, line: { width: 1 }, opacity: 1 } },
    },
  ];

  const traces = plot.buildTraces();
  assert.deepEqual(
    traces.map((trace) => [trace.name, trace.legendgroup, trace.showlegend]),
    [
      ["Short read", "dayoa:sr/arbitrary", true],
      ["Short read", "dayoa:sr/arbitrary", false],
      ["Long read", "dayoa:lr arbitrary", true],
    ],
  );
  assert.equal(plot.exportData("tsv"), "Name\tX\tY\nsr-one\t1\t2\nsr-two\t2\t3\nlr-one\t3\t4\n");
  assert.deepEqual(
    traces.map((trace) => trace.legendrank),
    [0, 0, 1],
  );
});

test("line traces use explicit grouping while exports retain original identifiers", () => {
  const plot = Object.create(window.LinePlot.prototype);
  plot.anchor = "mixed-line";
  plot.activeDatasetIdx = 0;
  plot.pconfig = {};
  plot.datasets = [
    {
      lines: [
        { name: "sr-one", pairs: [[1, 2]], color: "#111", dash: "solid", width: 1 },
        { name: "sr-two", pairs: [[1, 3]], color: "#222", dash: "solid", width: 1 },
        { name: "lr-one", pairs: [[1, 4]], color: "#333", dash: "solid", width: 1 },
      ],
      trace_params: {},
    },
  ];

  const traces = plot.buildTraces();
  assert.deepEqual(
    traces.map((trace) => [trace.name, trace.legendgroup, trace.showlegend]),
    [
      ["Short read", "dayoa:sr/arbitrary", true],
      ["Short read", "dayoa:sr/arbitrary", false],
      ["Long read", "dayoa:lr arbitrary", true],
    ],
  );
  assert.equal(plot.exportData("tsv"), "Sample\t1\nsr-one\t2\nsr-two\t3\nlr-one\t4\n");
  assert.deepEqual(
    traces.map((trace) => trace.legendrank),
    [0, 0, 1],
  );
});
