import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("changed, expected", [(False, 0), (True, 1)])
def test_changed_export_fails_even_with_identical_plot_table_payloads(tmp_path, monkeypatch, changed, expected):
    spec = importlib.util.spec_from_file_location(
        "bundle_comparison", Path(__file__).parents[1] / "scripts/compare_paginated_bundles.py"
    )
    comparison = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparison)
    baseline = {
        "manifest": {"pages": [{"anchor": "index"}, {"anchor": "metric"}]},
        "tables": {},
        "plots": {},
        "records": {},
        "groupings": {},
        "exports": {"values.tsv": "original"},
    }
    candidate = copy.deepcopy(baseline)
    candidate["manifest"]["pages"] = [{"anchor": "index", "sections": []}, {"anchor": "group", "sections": ["metric"]}]
    if changed:
        candidate["exports"]["values.tsv"] = "changed"
    monkeypatch.setattr(comparison, "inspect", lambda p: baseline if str(p) == "old" else candidate)
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(sys, "argv", ["compare", "--reference", "old", "--candidate", "new", "--receipt", str(receipt)])
    assert comparison.main() == expected
    result = json.loads(receipt.read_text())
    assert result["data_payload_rc"] == 0
    assert result["export_rc"] == expected
    assert result["rc"] == expected
