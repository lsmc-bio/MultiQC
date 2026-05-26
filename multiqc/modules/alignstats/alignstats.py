from __future__ import annotations

import logging
from typing import Dict, Mapping

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import bargraph, table
from multiqc.plots.table_object import ColumnDict

from .parser import native_sample_name, parse_combo_tsv, parse_native_report

log = logging.getLogger(__name__)


STAT_FAMILIES = {
    "Insert Size": ["InsertSizeMean", "InsertSizeMedian", "InsertSizeMode", "InsertSizeStandardDeviation"],
    "Aligned Read Length": [
        "AlignedReadLengthMean",
        "AlignedReadLengthMedian",
        "AlignedReadLengthMode",
        "AlignedReadLengthStandardDeviation",
    ],
    "WGS Coverage": ["WgsCoverageMean", "WgsCoverageMedian", "WgsCoverageStandardDeviation"],
    "Capture Coverage": ["CapCoverageMean", "CapCoverageMedian", "CapCoverageStandardDeviation"],
}


class MultiqcModule(BaseMultiqcModule):
    """
    Parses AlignStats key-value reports and combined MultiQC TSV exports.

    AlignStats produces alignment, WGS coverage, and capture coverage metrics
    for SAM, BAM, and CRAM inputs. This module shows read fate, coverage
    thresholds, and all available mean, median, mode, and standard deviation
    statistic families.
    """

    def __init__(self):
        super().__init__(
            name="AlignStats",
            anchor="alignstats",
            href="https://github.com/lsmc-bio/alignstats",
            info="Reports alignment, WGS coverage, capture coverage, and insert-size metrics.",
        )

        self.alignstats_data: Dict[str, Dict[str, object]] = {}
        self._sample_sources: Dict[str, str] = {}
        self._collect_combo()
        self._collect_native_reports()
        self.alignstats_data = self.ignore_samples(self.alignstats_data)
        if not self.alignstats_data:
            raise ModuleNoSamplesFound

        log.info(f"Found {len(self.alignstats_data)} AlignStats reports")
        self.add_software_version(None)
        self._add_general_stats()
        self._add_read_fate_section()
        self._add_coverage_section()
        self._add_stat_family_section()
        self._add_all_metrics_section()
        self.write_data_file(self.alignstats_data, "multiqc_alignstats")

    def _collect_combo(self) -> None:
        for f in self.find_log_files("alignstats/combo"):
            for sample, row in parse_combo_tsv(f["f"], f["fn"]).items():
                self._store_sample(sample, row, f)
                self.add_data_source(f, sample)

    def _collect_native_reports(self) -> None:
        for f in self.find_log_files("alignstats/json"):
            parsed = parse_native_report(f["f"], f["fn"])
            raw_sample = native_sample_name(f["fn"], f.get("root"), f["s_name"])
            sample = self.clean_s_name(raw_sample, f)
            self._store_sample(sample, parsed, f)
            self.add_data_source(f, sample)

    def _store_sample(self, sample: str, row: Dict[str, object], file_obj: Mapping[str, object]) -> None:
        source = "/".join(str(part).strip("/") for part in (file_obj.get("root", ""), file_obj.get("fn", "")) if part)
        if sample in self.alignstats_data:
            previous = self._sample_sources.get(sample, "unknown source")
            raise ValueError(f"Duplicate AlignStats sample '{sample}' from {source}; already parsed from {previous}")
        self.alignstats_data[sample] = row
        self._sample_sources[sample] = source

    def _add_general_stats(self) -> None:
        fields = {
            "MappedReadsPct": {"title": "Mapped Reads", "suffix": "%", "description": "Mapped reads as percent of yield reads"},
            "DuplicateReadsPct": {"title": "Duplicate Reads", "suffix": "%", "description": "Mapped duplicate reads as percent of mapped pass-QC reads"},
            "Q30BasesPct": {"title": "Q30 Bases", "suffix": "%", "description": "Q30 bases as percent of aligned bases"},
            "InsertSizeMedian": {"title": "Insert Median", "description": "Median observed insert size"},
            "WgsCoverageMean": {"title": "WGS Mean Cov", "suffix": "x", "description": "Mean WGS coverage"},
            "WgsCoverageMedian": {"title": "WGS Median Cov", "suffix": "x", "description": "Median WGS coverage"},
            "WgsCoverageBases30Pct": {"title": "WGS >=30x", "suffix": "%", "description": "Bases at or above 30x as percent of total bases"},
        }
        data = {
            sample: {key: to_number(row[key]) for key in fields if key in row}
            for sample, row in self.alignstats_data.items()
        }
        data = {sample: row for sample, row in data.items() if row}
        if data:
            self.general_stats_addcols(data, fields)

    def _add_read_fate_section(self) -> None:
        keys = ["MappedReadsPct", "UnmappedReadsPct", "DuplicateReadsPct", "FilteredRecordsPct"]
        self._add_bar_section("Read Fate", "alignstats-read-fate", keys, "Read fate percentages from AlignStats.")

    def _add_coverage_section(self) -> None:
        keys = [
            "WgsCoverageBases1Pct",
            "WgsCoverageBases10Pct",
            "WgsCoverageBases20Pct",
            "WgsCoverageBases30Pct",
            "WgsCoverageBases50Pct",
            "WgsCoverageBases100Pct",
        ]
        self._add_bar_section("WGS Coverage Thresholds", "alignstats-wgs-coverage", keys, "WGS coverage threshold percentages.")

    def _add_stat_family_section(self) -> None:
        rows: Dict[str, Dict[str, object]] = {}
        for sample, metrics in self.alignstats_data.items():
            row: Dict[str, object] = {}
            for keys in STAT_FAMILIES.values():
                for key in keys:
                    if key in metrics:
                        row[key] = to_number(metrics[key])
            if row:
                rows[sample] = row
        if rows:
            self.add_section(
                name="Statistic Families",
                anchor="alignstats-statistic-families",
                description="Mean, median, mode, and standard deviation metrics reported by AlignStats.",
                plot=table.plot(rows, table_headers(rows), {"id": "alignstats_statistic_families", "title": "Statistic Families"}),
            )

    def _add_all_metrics_section(self) -> None:
        self.add_section(
            name="All AlignStats Metrics",
            anchor="alignstats-all-metrics",
            description="All parsed AlignStats metrics.",
            plot=table.plot(
                self.alignstats_data,
                table_headers(self.alignstats_data),
                {"id": "alignstats_all_metrics", "title": "All AlignStats Metrics"},
            ),
        )

    def _add_bar_section(self, name: str, anchor: str, keys: list[str], description: str) -> None:
        available = set().union(*(row.keys() for row in self.alignstats_data.values())) if self.alignstats_data else set()
        used = [key for key in keys if key in available]
        if not used:
            return
        data = {
            sample: {key: to_number(row.get(key, 0)) for key in used}
            for sample, row in self.alignstats_data.items()
        }
        cats = {key: {"name": pretty_name(key)} for key in used}
        self.add_section(
            name=name,
            anchor=anchor,
            description=description,
            plot=bargraph.plot(data, cats, {"id": anchor.replace("-", "_"), "title": name}),
        )


def table_headers(rows: Mapping[str, Mapping[str, object]]) -> Dict[str, ColumnDict]:
    headers: Dict[str, ColumnDict] = {}
    for row in rows.values():
        for key in row:
            headers.setdefault(key, {"title": pretty_name(key)})
    return headers


def to_number(value: object) -> object:
    if value in {"", None}:
        return value
    text = str(value)
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return value


def pretty_name(value: str) -> str:
    return value.replace("_", " ").replace("Pct", " %").replace("Wgs", "WGS ").replace("Cap", "Capture ").strip()
