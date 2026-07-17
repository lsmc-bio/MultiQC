from pathlib import Path

import pytest

from multiqc import report, reset

from multiqc.modules.snakemake_benchmarks.parser import (
    aggregate_benchmarks,
    aggregate_rule_name,
    metric_distributions,
    parse_combined_benchmarks,
)


HEADER = "sample\trule\ts\th:m:s\tcpu_time\tsnakemake_threads\ttask_cost\n"
ROWS = (
    "S1\tsent.oct.1~1-50000000\t3600\t1:00:00\t1800\t4\t2.5\n"
    "S1\tsent.oct.2~50000001-100000000\t1800\t0:30:00\t900\t8\t1.5\n"
    "S1\tsent.dmd.alignstats\t600\t0:10:00\t300\t2\t0.5\n"
)


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("sent.oct.4~100000001-150000000", "sent.oct"),
        ("ont.clair3.17", "ont.clair3"),
        ("sent.sentd.1-24", "sent.sentd"),
        ("sent.dmd.alignstats", "sent.dmd.alignstats"),
    ],
)
def test_aggregate_rule_name_strips_only_terminal_shards(rule: str, expected: str) -> None:
    assert aggregate_rule_name(rule) == expected


def test_parse_and_aggregate_benchmarks() -> None:
    rows = parse_combined_benchmarks(HEADER + ROWS, "benchmarks.tsv")
    assert rows[0]["walltime_hours"] == 1.0
    assert rows[0]["observed_cpu_time_hours"] == 0.5
    assert rows[0]["allocated_vcpu_time_hours"] == 4.0

    summary = aggregate_benchmarks(rows)
    assert summary["sent.oct"]["executions"] == 2
    assert summary["sent.oct"]["walltime_hours_sum"] == 1.5
    assert summary["sent.oct"]["observed_cpu_time_hours_sum"] == 0.75
    assert summary["sent.oct"]["allocated_vcpu_time_hours_sum"] == 8.0
    assert summary["sent.oct"]["task_cost_usd_sum"] == 4.0
    assert metric_distributions(rows, "task_cost")["sent.oct"] == [2.5, 1.5]


def test_combined_benchmark_requires_authoritative_cost_and_timing_columns() -> None:
    with pytest.raises(ValueError, match="missing required column.*task_cost"):
        parse_combined_benchmarks(HEADER.replace("\ttask_cost", "") + "S1\trule\t1\t0:00:01\t1\t1\n", "bad.tsv")

    with pytest.raises(ValueError, match="missing required column.*sample"):
        parse_combined_benchmarks(HEADER.replace("sample\t", "") + "rule\t1\t0:00:01\t1\t1\t0.1\n", "bad.tsv")


@pytest.mark.parametrize(
    ("column", "value"), [("s", "bad"), ("cpu_time", "-1"), ("snakemake_threads", "0"), ("task_cost", "nan")]
)
def test_combined_benchmark_rejects_malformed_metrics(column: str, value: str) -> None:
    fields = HEADER.strip().split("\t")
    row = dict(zip(fields, ["S1", "rule", "1", "0:00:01", "1", "1", "0.1"]))
    row[column] = value
    text = HEADER + "\t".join(row[field] for field in fields) + "\n"
    with pytest.raises(ValueError):
        parse_combined_benchmarks(text, "bad.tsv")


def test_combined_benchmark_rejects_header_only_file() -> None:
    with pytest.raises(ValueError, match="no data rows"):
        parse_combined_benchmarks(HEADER, "empty.tsv")


def test_missing_cpu_threads_and_cost_are_explicit_and_not_zero_filled() -> None:
    row = "S1\trule\t60\t0:01:00\tNA\tNA\t\n"
    rows = parse_combined_benchmarks(HEADER + row, "benchmarks.tsv")
    assert rows[0]["observed_cpu_time_hours"] is None
    assert rows[0]["allocated_vcpu_time_hours"] is None
    assert rows[0]["task_cost"] is None

    summary = aggregate_benchmarks(rows)["rule"]
    assert summary["walltime_hours_rows"] == 1
    assert summary["observed_cpu_time_hours_rows"] == 0
    assert summary["allocated_vcpu_time_hours_sum"] is None
    assert summary["task_cost_usd_sum"] is None


def test_shifted_dayoa_root_benchmark_path_row_fails_hard() -> None:
    header = (
        "combined_rule\tsample\trule\ts\th:m:s\tmax_rss\tmax_vms\tmax_uss\tmax_pss\tio_in\tio_out\t"
        "mean_load\tcpu_time\thostname\tip\tnproc\tcpu_efficiency\tinstance_type\tregion_az\tspot_cost\t"
        "snakemake_threads\ttask_cost\trule_prefix\trule_suffix\n"
    )
    row = (
        "0.0053-results/day/hg38/benchmarks/aggregate_report_components.bench.tsv\t"
        "results/day/hg38/benchmarks/aggregate_report_components.bench.tsv\t"
        "0.0053\t0:00:00\t2.16\t6.11\t0.20\t0.24\t0\t0\t0\t0\t"
        "host\t10.0.0.1\t16\t0\tr7i.4xlarge\tus-west-2d\t0.3633\t2\t0.000001\t\t0\t0053\n"
    )
    with pytest.raises(ValueError, match="Combined benchmark s must be numeric"):
        parse_combined_benchmarks(header + row, "rules_benchmark_data_mqc.tsv")


def test_valid_dayoa_24_column_raw_row_parses_without_projection() -> None:
    header = (
        "combined_rule\tsample\trule\ts\th:m:s\tmax_rss\tmax_vms\tmax_uss\tmax_pss\tio_in\tio_out\t"
        "mean_load\tcpu_time\thostname\tip\tnproc\tcpu_efficiency\tinstance_type\tregion_az\tspot_cost\t"
        "snakemake_threads\ttask_cost\trule_prefix\trule_suffix\n"
    )
    row = (
        "sent.oct.1-S1\tS1\tsent.oct.1~1-50000000\t60\t0:01:00\t2.16\t6.11\t0.20\t0.24\t0\t0\t"
        "50\t30\thost\t10.0.0.1\t16\t50\tr7i.4xlarge\tus-west-2d\t0.3633\t2\t0.01\tsent.oct\t1\n"
    )

    parsed = parse_combined_benchmarks(header + row, "benchmarks_summary.tsv")

    assert parsed[0]["aggregate_rule"] == "sent.oct"
    assert parsed[0]["walltime_hours"] == pytest.approx(1 / 60)
    assert parsed[0]["observed_cpu_time_hours"] == pytest.approx(30 / 3600)
    assert parsed[0]["allocated_vcpu_time_hours"] == pytest.approx(2 / 60)
    assert parsed[0]["task_cost"] == pytest.approx(0.01)


def test_module_deduplicates_identical_combined_inputs(tmp_path: Path) -> None:
    contents = HEADER + ROWS
    (tmp_path / "benchmarks.tsv").write_text(contents)
    (tmp_path / "benchmarks_summary.tsv").write_text(contents)

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["snakemake_benchmarks"])

    from multiqc.modules.snakemake_benchmarks.snakemake_benchmarks import MultiqcModule

    module = MultiqcModule()
    assert module.summary["sent.oct"]["executions"] == 2
    assert len(module.raw_rows) == 3


def test_module_rejects_conflicting_combined_inputs_with_all_paths(tmp_path: Path) -> None:
    (tmp_path / "benchmarks.tsv").write_text(HEADER + ROWS)
    (tmp_path / "benchmarks_summary.tsv").write_text(HEADER + ROWS.replace("3600", "3601", 1))

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["snakemake_benchmarks"])

    from multiqc.modules.snakemake_benchmarks.snakemake_benchmarks import MultiqcModule

    with pytest.raises(ValueError) as exc_info:
        MultiqcModule()
    message = str(exc_info.value)
    assert "Conflicting normalized Snakemake benchmark inputs" in message
    assert "benchmarks.tsv" in message
    assert "benchmarks_summary.tsv" in message
