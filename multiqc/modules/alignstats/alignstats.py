import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Mapping, Union

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import bargraph, table
from multiqc.plots.table_object import ColumnDict
from .parser import AlignstatsValue, native_sample_name, parse_combo_tsv, parse_native_report

log = logging.getLogger(__name__)
GeneralStatValue = Union[int, float, str, bool]


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
            doi=None,
        )

        self._sample_rows: Dict[str, Dict[str, Dict[str, AlignstatsValue]]] = {}
        self._sample_sources: Dict[str, Dict[str, List[str]]] = {}
        self._collect_combo()
        self._collect_native_reports()
        self.alignstats_data = self._reconcile_samples()
        self.alignstats_data = self.ignore_samples(self.alignstats_data)
        if not self.alignstats_data:
            raise ModuleNoSamplesFound

        self._register_reconciled_data_sources()

        log.info(f"Found {len(self.alignstats_data)} AlignStats reports")
        self.add_software_version(None)
        self._add_general_stats()
        self._add_read_fate_section()
        self._add_coverage_section()
        self._add_stat_family_section()
        self._add_all_metrics_section()
        self.write_data_file(self.alignstats_data, "multiqc_alignstats")
        self.write_data_file(self._sample_sources, "multiqc_alignstats_input_provenance")

    def _collect_combo(self) -> None:
        for f in self.find_log_files("alignstats/combo"):
            for sample, row in parse_combo_tsv(f["f"], f["fn"]).items():
                self._store_representation(sample, row, f, "combined TSV")

    def _collect_native_reports(self) -> None:
        for f in self.find_log_files("alignstats/json"):
            parsed = parse_native_report(f["f"], f["fn"])
            raw_sample = native_sample_name(f["fn"], f.get("root"), f["s_name"])
            sample = self.clean_s_name(raw_sample, f)
            self._store_representation(sample, parsed, f, "native report")

    def _register_reconciled_data_sources(self) -> None:
        """Register one deterministic path per logical sample after reconciliation.

        Repeated identical files remain fully represented in the provenance data,
        while MultiQC's one-path-per-sample source index receives only the first
        normalized source path. Deferring this until after reconciliation also
        prevents physical duplicates from being mistaken for duplicate samples.
        """
        for sample in sorted(self.alignstats_data):
            paths = sorted(
                source
                for representation_sources in self._sample_sources[sample].values()
                for source in representation_sources
            )
            if not paths:
                raise AssertionError(f"AlignStats sample has no source paths: {sample}")
            self.add_data_source(s_name=sample, path=paths[0])

    def _store_representation(
        self,
        sample: str,
        row: Dict[str, AlignstatsValue],
        file_obj: Mapping[str, object],
        representation: str,
    ) -> None:
        source = source_path(file_obj)
        sample_rows = self._sample_rows.setdefault(sample, {})
        sample_sources = self._sample_sources.setdefault(sample, {}).setdefault(representation, [])
        if representation in sample_rows and not rows_equal(sample_rows[representation], row):
            paths = sorted([*sample_sources, source])
            raise ValueError(
                f"Conflicting AlignStats {representation} inputs for sample '{sample}': {', '.join(paths)}"
            )
        sample_rows.setdefault(representation, row)
        sample_sources.append(source)

    def _reconcile_samples(self) -> Dict[str, Dict[str, AlignstatsValue]]:
        reconciled: Dict[str, Dict[str, AlignstatsValue]] = {}
        for sample, representations in self._sample_rows.items():
            combined = representations.get("combined TSV")
            native = representations.get("native report")
            if combined is None:
                assert native is not None
                reconciled[sample] = dict(native)
                continue
            if native is None:
                reconciled[sample] = dict(combined)
                continue

            conflicts = sorted(
                key
                for key in set(combined) & set(native)
                if normalized_value(combined[key]) != normalized_value(native[key])
            )
            if conflicts:
                paths = sorted(
                    source
                    for representation_sources in self._sample_sources[sample].values()
                    for source in representation_sources
                )
                raise ValueError(
                    f"Conflicting AlignStats combined TSV and native report fields for sample '{sample}' "
                    f"({', '.join(conflicts)}): {', '.join(paths)}"
                )
            reconciled[sample] = {**combined, **{key: value for key, value in native.items() if key not in combined}}
        return reconciled

    def _add_general_stats(self) -> None:
        fields = {
            "MappedReadsPct": {
                "title": "Mapped Reads",
                "suffix": "%",
                "description": "Mapped reads as percent of yield reads",
            },
            "DuplicateReadsPct": {
                "title": "Duplicate Reads",
                "suffix": "%",
                "description": "Mapped duplicate reads as percent of mapped pass-QC reads",
            },
            "Q30BasesPct": {
                "title": "Q30 Bases",
                "suffix": "%",
                "description": "Q30 bases as percent of aligned bases",
            },
            "InsertSizeMedian": {"title": "Insert Median", "description": "Median observed insert size"},
            "WgsCoverageMean": {"title": "WGS Mean Cov", "suffix": "x", "description": "Mean WGS coverage"},
            "WgsCoverageMedian": {"title": "WGS Median Cov", "suffix": "x", "description": "Median WGS coverage"},
            "WgsCoverageBases30Pct": {
                "title": "WGS >=30x",
                "suffix": "%",
                "description": "Bases at or above 30x as percent of total bases",
            },
        }
        data: Dict[str, Dict[str, GeneralStatValue]] = {}
        for sample, row in self.alignstats_data.items():
            sample_data: Dict[str, GeneralStatValue] = {}
            for key in fields:
                if key in row:
                    value = to_number(row[key])
                    if value is not None:
                        sample_data[key] = value
            data[sample] = sample_data
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
        self._add_bar_section(
            "WGS Coverage Thresholds", "alignstats-wgs-coverage", keys, "WGS coverage threshold percentages."
        )

    def _add_stat_family_section(self) -> None:
        rows: Dict[str, Dict[str, AlignstatsValue]] = {}
        for sample, metrics in self.alignstats_data.items():
            row: Dict[str, AlignstatsValue] = {}
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
                plot=table.plot(
                    rows, table_headers(rows), {"id": "alignstats_statistic_families", "title": "Statistic Families"}
                ),
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
        available = (
            set().union(*(row.keys() for row in self.alignstats_data.values())) if self.alignstats_data else set()
        )
        used = [key for key in keys if key in available]
        if not used:
            return
        data = {
            sample: {key: to_number(row[key]) for key in used if key in row}
            for sample, row in self.alignstats_data.items()
        }
        cats = {key: {"name": pretty_name(key)} for key in used}
        self.add_section(
            name=name,
            anchor=anchor,
            description=description,
            plot=bargraph.plot(data, cats, {"id": anchor.replace("-", "_"), "title": name}),
        )


def table_headers(rows: Mapping[str, Mapping[str, AlignstatsValue]]) -> Dict[str, ColumnDict]:
    headers: Dict[str, ColumnDict] = {}
    for row in rows.values():
        for key in row:
            headers.setdefault(key, {"title": pretty_name(key)})
    return headers


def source_path(file_obj: Mapping[str, object]) -> str:
    return os.path.join(str(file_obj.get("root", "")), str(file_obj.get("fn", "")))


def normalized_value(value: AlignstatsValue) -> object:
    if isinstance(value, bool) or value is None:
        return value
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return str(value)


def rows_equal(left: Mapping[str, AlignstatsValue], right: Mapping[str, AlignstatsValue]) -> bool:
    return set(left) == set(right) and all(normalized_value(left[key]) == normalized_value(right[key]) for key in left)


def to_number(value: AlignstatsValue) -> AlignstatsValue:
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
