import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

globalThis.window = {};
globalThis.Plot = class {};

const scatterSource = readFileSync(new URL("../src/js/plots/scatter.js", import.meta.url), "utf8");
vm.runInThisContext(scatterSource, { filename: "scatter.js" });

function makePlot(settings) {
  globalThis.applyToolboxSettings = () => settings;

  const plot = Object.create(window.ScatterPlot.prototype);
  plot.datasets = [
    {
      points: [
        { name: "sr-visible", x: 1, y: 2 },
        { name: "lr-hidden", x: 3, y: 4 },
        { name: "hybrid-visible", x: 5, y: 6 },
      ],
      trace_params: {
        marker: {
          size: 5,
          line: { width: 1 },
          opacity: 1,
          color: "#123456",
          symbol: "circle",
        },
      },
    },
  ];
  plot.activeDatasetIdx = 0;
  plot.pconfig = {};
  return plot;
}

test("hidden scatter points are removed without misaligning traces or exports", () => {
  const plot = makePlot([
    { name: "sr-visible", pseudonym: null, highlight: null, hidden: false },
    { name: "lr-hidden", pseudonym: null, highlight: null, hidden: true },
    { name: "hybrid-visible", pseudonym: null, highlight: "#ff0000", hidden: false },
  ]);

  const errors = [];
  const originalConsoleError = console.error;
  console.error = (...args) => errors.push(args);

  try {
    const [samples, points] = plot.prepData();
    assert.deepEqual(samples, ["sr-visible", "hybrid-visible"]);
    assert.deepEqual(
      points.map((point) => point.name),
      samples,
    );
    assert.equal(points.includes(undefined), false);

    const traces = plot.buildTraces();
    assert.deepEqual(
      traces.map((trace) => trace.text[0]),
      ["sr-visible", "hybrid-visible"],
    );
    assert.equal(plot.exportData("tsv"), "Name\tX\tY\nsr-visible\t1\t2\nhybrid-visible\t5\t6\n");
    assert.deepEqual(errors, []);
  } finally {
    console.error = originalConsoleError;
  }
});

test("an all-hidden scatter dataset renders no traces and exports only its header", () => {
  const plot = makePlot([
    { name: "sr-visible", pseudonym: null, highlight: null, hidden: true },
    { name: "lr-hidden", pseudonym: null, highlight: null, hidden: true },
    { name: "hybrid-visible", pseudonym: null, highlight: null, hidden: true },
  ]);

  assert.deepEqual(plot.prepData(), [[], []]);
  assert.deepEqual(plot.buildTraces(), []);
  assert.equal(plot.exportData("tsv"), "Name\tX\tY\n");
});
