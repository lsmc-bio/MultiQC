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
        "{\n"
        '    "InputFile": "HG003.bam",\n'
        '    "MappedReads": 100,\n'
        '    "MappedReadsPct": 99.1,\n'
        '    "WgsCoverageMean": 31.2\n'
        "}\n"
    )

    report.analysis_files = [str(tmp_path)]
    report.search_files(["alignstats"])

    from multiqc.modules.alignstats.alignstats import MultiqcModule

    module = MultiqcModule()
    assert module.alignstats_data["HG003"]["WgsCoverageMean"] == 31.2


def test_module_deduplicates_identical_combined_inputs(tmp_path: Path) -> None:
    contents = "Sample\tMappedReadsPct\tWgsCoverageMean\nHG003\t99.1\t31.2\n"
    (tmp_path / "one_alignstats_combo_mqc.tsv").write_text(contents)
    (tmp_path / "two_alignstats_combo_mqc.tsv").write_text(contents)
    (tmp_path / "alignstats_gs_mqc.tsv").write_text(contents)

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["alignstats"])

    from multiqc.modules.alignstats.alignstats import MultiqcModule

    module = MultiqcModule()
    assert module.alignstats_data == {"HG003": {"MappedReadsPct": "99.1", "WgsCoverageMean": "31.2"}}


def test_module_reconciles_combined_and_native_metrics(tmp_path: Path) -> None:
    (tmp_path / "alignstats_combo_mqc.tsv").write_text("Sample\tMappedReadsPct\tWgsCoverageMean\nHG003\t99.10\t31.2\n")
    (tmp_path / "HG003.alignstats.json").write_text(
        '{"MappedReads": 100, "MappedReadsPct": 99.1, "WgsCoverageMean": 31.20, "WgsCoverageMedian": 31}'
    )

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["alignstats"])

    from multiqc.modules.alignstats.alignstats import MultiqcModule

    module = MultiqcModule()
    assert module.alignstats_data["HG003"]["MappedReadsPct"] == "99.10"
    assert module.alignstats_data["HG003"]["MappedReads"] == 100
    assert module.alignstats_data["HG003"]["WgsCoverageMedian"] == 31


def test_module_rejects_conflicting_combined_and_native_metrics_with_paths(tmp_path: Path) -> None:
    (tmp_path / "alignstats_combo_mqc.tsv").write_text("Sample\tMappedReadsPct\nHG003\t99.1\n")
    (tmp_path / "HG003.alignstats.json").write_text('{"MappedReads": 100, "MappedReadsPct": 98.0}')

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["alignstats"])

    from multiqc.modules.alignstats.alignstats import MultiqcModule

    with pytest.raises(ValueError) as exc_info:
        MultiqcModule()
    message = str(exc_info.value)
    assert "MappedReadsPct" in message
    assert "alignstats_combo_mqc.tsv" in message
    assert "HG003.alignstats.json" in message
