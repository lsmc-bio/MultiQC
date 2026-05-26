from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from multiqc import report, reset


def _load_parser():
    parser_path = Path(__file__).resolve().parents[1] / "parser.py"
    spec = importlib.util.spec_from_file_location("alignstats_parser_under_test", parser_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_parser = _load_parser()
native_sample_name = _parser.native_sample_name
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

    with pytest.raises(ValueError, match="recognized AlignStats metrics"):
        parse_native_report('{"InputFile": "sample.bam"}', "not-alignstats-report.json")


def test_native_sample_name_uses_parent_for_generic_reports() -> None:
    assert native_sample_name("HG003.alignstats.json", "/work/ignored", "fallback") == "HG003"
    assert native_sample_name("report.txt", "/work/HG003", "report") == "HG003"
    assert native_sample_name("alignstats.json", "/work/HG004", "alignstats") == "HG004"


def test_parse_combo_tsv_rejects_duplicate_samples() -> None:
    with pytest.raises(ValueError, match="Duplicate AlignStats sample"):
        parse_combo_tsv(
            "Sample\tMappedReadsPct\nHG003.sent\t99.1\nHG003.sent\t99.2\n",
            "alignstats_combo_mqc.tsv",
        )


def test_module_autodetects_generic_native_report(tmp_path: Path) -> None:
    reset()
    sample_dir = tmp_path / "HG003"
    sample_dir.mkdir()
    (sample_dir / "report.txt").write_text(
        '{\n'
        '    "InputFile": "HG003.bam",\n'
        '    "MappedReads": 100,\n'
        '    "MappedReadsPct": 99.1,\n'
        '    "WgsCoverageMean": 31.2\n'
        '}\n'
    )

    report.analysis_files = [tmp_path]
    report.search_files(["alignstats"])

    from multiqc.modules.alignstats.alignstats import MultiqcModule

    module = MultiqcModule()
    assert module.alignstats_data["HG003"]["WgsCoverageMean"] == 31.2
