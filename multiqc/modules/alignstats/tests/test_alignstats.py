from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_parser():
    parser_path = Path(__file__).resolve().parents[1] / "parser.py"
    spec = importlib.util.spec_from_file_location("alignstats_parser_under_test", parser_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_parser = _load_parser()
parse_combo_tsv = _parser.parse_combo_tsv
parse_native_report = _parser.parse_native_report


def test_parse_combo_tsv_supports_all_stat_family_columns() -> None:
    rows = parse_combo_tsv(
        "Sample\taligner\tMappedReadsPct\tInsertSizeMean\tInsertSizeMedian\tInsertSizeMode\t"
        "InsertSizeStandardDeviation\tWgsCoverageMean\tWgsCoverageMedian\tWgsCoverageStandardDeviation\n"
        "HG003.sent.dmd\tsent\t99.1\t350.4\t349\t350\t22.1\t31.2\t31\t4.2\n",
        "alignstats_combo_mqc.tsv",
    )

    row = rows["HG003.sent.dmd"]
    assert row["InsertSizeMean"] == "350.4"
    assert row["InsertSizeMedian"] == "349"
    assert row["InsertSizeMode"] == "350"
    assert row["InsertSizeStandardDeviation"] == "22.1"
    assert row["WgsCoverageStandardDeviation"] == "4.2"


def test_parse_native_report_requires_json_object() -> None:
    parsed = parse_native_report('{"WgsCoverageMean": 31.2, "MappedReadsPct": 99.1}', "HG003.alignstats.json")
    assert parsed["WgsCoverageMean"] == 31.2

    with pytest.raises(ValueError, match="not valid JSON-like"):
        parse_native_report("WgsCoverageMean 31.2", "bad.alignstats.txt")

    with pytest.raises(ValueError, match="must be an object"):
        parse_native_report("[1, 2]", "bad.alignstats.json")


def test_parse_combo_tsv_rejects_duplicate_samples() -> None:
    with pytest.raises(ValueError, match="Duplicate AlignStats sample"):
        parse_combo_tsv(
            "Sample\tMappedReadsPct\nHG003.sent\t99.1\nHG003.sent\t99.2\n",
            "alignstats_combo_mqc.tsv",
        )
