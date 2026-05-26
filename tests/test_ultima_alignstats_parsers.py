from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_parser(path: str, module_name: str):
    parser_path = REPO_ROOT / path
    spec = importlib.util.spec_from_file_location(module_name, parser_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ultima_parser = _load_parser("multiqc/modules/ultima/parser.py", "ultima_parser_root_test")
alignstats_parser = _load_parser("multiqc/modules/alignstats/parser.py", "alignstats_parser_root_test")


def test_ultima_parser_requires_sample_first_column() -> None:
    rows = ultima_parser.parse_sample_first_tsv(
        "Sample\trun_id\tobserved_outputs\tmissing_required_outputs\n"
        "602202.Z0157.FAKE_SAMPLE_1\t602202\t9\t0\n",
        "ultima_demux_summary_mqc.tsv",
    )

    assert rows["602202.Z0157.FAKE_SAMPLE_1"]["observed_outputs"] == "9"

    with pytest.raises(ValueError, match="Unsafe Ultima Sample"):
        ultima_parser.parse_sample_first_tsv("Sample\trun_id\nR1\t602202\n", "ultima_run_inventory_mqc.tsv")

    with pytest.raises(ValueError, match="Duplicate Ultima Sample"):
        ultima_parser.parse_sample_first_tsv("Sample\trun_id\n602202\t602202\n602202\t602202\n", "ultima_run_inventory_mqc.tsv")


def test_alignstats_parser_preserves_stat_family_columns() -> None:
    rows = alignstats_parser.parse_combo_tsv(
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


def test_alignstats_native_json_parser() -> None:
    parsed = alignstats_parser.parse_native_report(
        '{"WgsCoverageMean": 31.2, "MappedReadsPct": 99.1}',
        "HG003.alignstats.json",
    )
    assert parsed["WgsCoverageMean"] == 31.2

    with pytest.raises(ValueError, match="not valid JSON-like"):
        alignstats_parser.parse_native_report("WgsCoverageMean 31.2", "bad.alignstats.txt")

    with pytest.raises(ValueError, match="Duplicate AlignStats sample"):
        alignstats_parser.parse_combo_tsv("Sample\tMappedReadsPct\nHG003.sent\t99.1\nHG003.sent\t99.2\n", "alignstats_combo_mqc.tsv")
