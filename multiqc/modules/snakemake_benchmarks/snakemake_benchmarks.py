import logging
import os
from typing import Dict, Mapping, Sequence

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import box, table
from multiqc.plots.table_object import ColumnDict
from multiqc.types import SectionAlert

from .parser import Value, aggregate_benchmarks, metric_distributions, parse_combined_benchmarks

log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    """
    Snakemake Benchmarks aggregates a combined workflow benchmark TSV by rule.

    The module recognizes `benchmarks.tsv`, `benchmarks_summary.tsv`, and
    `rules_benchmark_data_mqc.tsv`. Repeated inputs must normalize to identical
    rows; contradictory inputs fail with every source path.
    Required columns are `sample`, `rule`, `s`, `cpu_time`,
    `snakemake_threads`, and `task_cost`.

    Dynamic terminal shard suffixes such as `.17`, `.1-24`, and
    `.4~100000001-150000000` are removed to form the aggregate rule name.
    Other rule-name components are preserved.

    Every row must follow the declared header shape. Shifted collector rows,
    including rows with elapsed `h:m:s` text in the numeric `s` column, fail
    hard instead of being reinterpreted or skipped.

    For each aggregate rule, the report shows execution count and the sum,
    mean, median, minimum, and maximum of:

    - walltime hours, calculated as `s / 3600`;
    - observed CPU time hours, calculated as `cpu_time / 3600`;
    - allocated vCPU time hours, calculated as
      `s * snakemake_threads / 3600`;
    - task cost in USD, taken directly from `task_cost`.

    Boxplots show per-execution distributions. Task cost does not include
    cluster startup, pending time, controller time, storage, or other costs
    absent from the combined input.
    """

    def __init__(self):
        super().__init__(
            name="Snakemake Benchmarks",
            anchor="snakemake-benchmarks",
            href="https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#benchmark-rules",
            info="Aggregates rule walltime, observed CPU time, allocated vCPU time, and task cost from combined Snakemake benchmarks.",
            doi="10.1093/bioinformatics/bts480",
        )

        files = list(self.find_log_files("snakemake_benchmarks/combined"))
        if not files:
            raise ModuleNoSamplesFound
        raw_rows = parse_combined_benchmarks(files[0]["f"], files[0]["fn"])
        for source in files[1:]:
            candidate_rows = parse_combined_benchmarks(source["f"], source["fn"])
            if candidate_rows != raw_rows:
                paths = sorted(source_path(item) for item in files)
                raise ValueError(f"Conflicting normalized Snakemake benchmark inputs: {', '.join(paths)}")
        summary = aggregate_benchmarks(raw_rows)
        summary = self.ignore_samples(summary)
        if not summary:
            raise ModuleNoSamplesFound
        raw_rows = [row for row in raw_rows if str(row["aggregate_rule"]) in summary]
        for aggregate_rule in summary:
            self.add_data_source(files[0], s_name=aggregate_rule, section="aggregate_rules")

        self.summary = summary
        self.raw_rows = {f"row_{index + 1}": row for index, row in enumerate(raw_rows)}
        self.input_provenance = {
            aggregate_rule: {"source_paths": sorted(source_path(source) for source in files)}
            for aggregate_rule in summary
        }
        log.info("Found %d benchmark rows across %d aggregate rules", len(raw_rows), len(summary))
        self.add_software_version(None)
        self._add_summary_table()
        self._add_boxplot(
            raw_rows,
            metric="walltime_hours",
            name="Walltime by Aggregate Rule",
            anchor="snakemake-benchmarks-walltime",
            title="Snakemake Benchmarks: Walltime",
            xlab="Walltime (hours)",
        )
        self._add_boxplot(
            raw_rows,
            metric="allocated_vcpu_time_hours",
            name="Allocated vCPU Time by Aggregate Rule",
            anchor="snakemake-benchmarks-vcpu-time",
            title="Snakemake Benchmarks: Allocated vCPU Time",
            xlab="Allocated vCPU time (hours)",
        )
        self._add_boxplot(
            raw_rows,
            metric="observed_cpu_time_hours",
            name="Observed CPU Time by Aggregate Rule",
            anchor="snakemake-benchmarks-cpu-time",
            title="Snakemake Benchmarks: Observed CPU Time",
            xlab="Observed CPU time (hours)",
        )
        self._add_boxplot(
            raw_rows,
            metric="task_cost",
            name="Task Cost by Aggregate Rule",
            anchor="snakemake-benchmarks-task-cost",
            title="Snakemake Benchmarks: Task Cost",
            xlab="Task cost (USD)",
        )
        self.write_data_file(self.summary, "multiqc_snakemake_benchmark_aggregate_rules")
        self.write_data_file(self.raw_rows, "multiqc_snakemake_benchmark_rows")
        self.write_data_file(self.input_provenance, "multiqc_snakemake_benchmark_input_provenance")

    def _add_summary_table(self) -> None:
        self.add_section(
            name="Aggregate Rule Summary",
            anchor="snakemake-benchmarks-summary",
            description=(
                "Combined benchmark rows aggregated by normalized rule name. Allocated vCPU time is walltime "
                "multiplied by requested Snakemake threads. Cost is summed directly from task_cost."
            ),
            plot=table.plot(
                self.summary,
                summary_headers(),
                {
                    "id": "snakemake_benchmark_summary",
                    "title": "Snakemake Benchmark Aggregate Rules",
                    "no_violin": True,
                },
            ),
        )

    def _add_boxplot(
        self,
        rows: Sequence[Mapping[str, Value]],
        metric: str,
        name: str,
        anchor: str,
        title: str,
        xlab: str,
    ) -> None:
        distributions = metric_distributions(rows, metric)
        missing_rules = sorted(set(self.summary) - set(distributions))
        self.add_section(
            name=name,
            anchor=anchor,
            description="Per-execution distribution for each aggregate rule in the combined benchmark input.",
            plot=(
                box.plot(
                    distributions,
                    {
                        "id": anchor.replace("-", "_"),
                        "title": title,
                        "xlab": xlab,
                        "sort_by_median": True,
                        "boxpoints": "all",
                    },
                )
                if distributions
                else None
            ),
            alerts=(
                SectionAlert(
                    message=(
                        f"**{len(missing_rules)} aggregate rule{'s' if len(missing_rules) != 1 else ''}** "
                        "had no numeric values for this metric. Missing values were not coerced to zero."
                    ),
                    level="warning",
                    affected_samples=missing_rules,
                )
                if missing_rules
                else None
            ),
        )


def summary_headers() -> Dict[str, ColumnDict]:
    return {
        "executions": {"title": "Executions", "description": "Combined benchmark rows in this aggregate rule"},
        "walltime_hours_rows": {"title": "Walltime Rows", "hidden": True},
        "walltime_hours_sum": {"title": "Walltime Sum", "suffix": " h"},
        "walltime_hours_mean": {"title": "Walltime Mean", "suffix": " h"},
        "walltime_hours_median": {"title": "Walltime Median", "suffix": " h"},
        "walltime_hours_min": {"title": "Walltime Min", "suffix": " h", "hidden": True},
        "walltime_hours_max": {"title": "Walltime Max", "suffix": " h", "hidden": True},
        "observed_cpu_time_hours_rows": {"title": "CPU Time Rows"},
        "observed_cpu_time_hours_sum": {"title": "CPU Time Sum", "suffix": " h"},
        "observed_cpu_time_hours_mean": {"title": "CPU Time Mean", "suffix": " h", "hidden": True},
        "observed_cpu_time_hours_median": {"title": "CPU Time Median", "suffix": " h"},
        "observed_cpu_time_hours_min": {"title": "CPU Time Min", "suffix": " h", "hidden": True},
        "observed_cpu_time_hours_max": {"title": "CPU Time Max", "suffix": " h", "hidden": True},
        "allocated_vcpu_time_hours_rows": {"title": "vCPU Time Rows"},
        "allocated_vcpu_time_hours_sum": {"title": "vCPU Time Sum", "suffix": " h"},
        "allocated_vcpu_time_hours_mean": {"title": "vCPU Time Mean", "suffix": " h", "hidden": True},
        "allocated_vcpu_time_hours_median": {"title": "vCPU Time Median", "suffix": " h"},
        "allocated_vcpu_time_hours_min": {"title": "vCPU Time Min", "suffix": " h", "hidden": True},
        "allocated_vcpu_time_hours_max": {"title": "vCPU Time Max", "suffix": " h", "hidden": True},
        "task_cost_usd_rows": {"title": "Cost Rows"},
        "task_cost_usd_sum": {"title": "Cost Sum", "format": "${:,.4f}"},
        "task_cost_usd_mean": {"title": "Cost Mean", "format": "${:,.4f}", "hidden": True},
        "task_cost_usd_median": {"title": "Cost Median", "format": "${:,.4f}"},
        "task_cost_usd_min": {"title": "Cost Min", "format": "${:,.4f}", "hidden": True},
        "task_cost_usd_max": {"title": "Cost Max", "format": "${:,.4f}", "hidden": True},
    }


def source_path(file_obj: Mapping[str, object]) -> str:
    return os.path.join(str(file_obj.get("root", "")), str(file_obj.get("fn", "")))
