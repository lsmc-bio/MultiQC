import hashlib
import json
import logging
import os
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import table
from multiqc.plots.table_object import ColumnDict
from multiqc.types import LoadedFileDict

from .parser import (
    HYBRID_REQUIRED_COLUMNS,
    evaluate_hybrid_qc,
    parse_analysis_unit_inputs,
    parse_analysis_units,
    parse_libraries,
    parse_gender_checks,
    parse_hybrid_qc,
    parse_samples,
    parse_sequencing_inputs,
    parse_specimens,
    resolve_analysis_units,
    validate_gender_samples,
    validate_manifest_lineage,
    Value,
)

log = logging.getLogger(__name__)

STATUS_COLORS = {"PASS": "#d1e7dd", "FAIL": "#f8d7da"}


class MultiqcModule(BaseMultiqcModule):
    """
    Snakemake Specimens / Samples / Libraries / Inputs / Analysis Units
    reports the exact DayOA 13 six-manifest model.

    Five entity manifests retain their source grains and keys:

    - `specimens.tsv`, keyed by `SPECIMEN_ID`.
    - `samples.tsv`, keyed by `SAMPLEID` with a specimen foreign key.
    - `libraries.tsv`, keyed by physical `LIBRARY_ID` with a sample foreign key.
    - `sequencing_inputs.tsv`, keyed by `SEQUENCING_INPUT_UID` with exact
      `LIBRARY_ID`, `MODALITY`, and `LAYOUT` fields.
    - `analysis_units.tsv`, keyed by `ANALYSIS_UNIT_UID` with a sample foreign key.

    `analysis_unit_inputs.tsv` is the required ordered many-to-many join. It
    retains exact analysis-unit and sequencing-input identifiers, `ROLE`, and
    canonical `INPUT_ORDINAL`. The analysis-unit section also exposes resolved
    ordered library, input, role, modality, and layout arrays derived solely
    from this join.

    The optional `reported_vs_inferred_sex_check_mqc.tsv` retains sex-check
    evidence. The optional `hybrid_seq_batch_qc.tsv` has one schema version 1
    row for every `analysis_units.tsv` row. Required columns are:

      `schema_version`, `analysis_unit_uid`, `sample_id`,
      `contamination_estimate_pct`, `contamination_max_pct`,
      `short_read_coverage_threshold`,
      `short_read_bases_above_threshold_pct`,
      `short_read_bases_above_threshold_pct_min`, `long_read_mean_coverage`,
      `long_read_mean_coverage_min`, `long_read_target_10x_pct`,
      `long_read_target_10x_pct_min`, `short_read_target_coverage_threshold`,
      `short_read_target_below_threshold_pct`,
      `short_read_target_below_threshold_pct_max`,
      `hybrid_callable_target_snvs_pct`,
      `hybrid_callable_target_snvs_pct_min`, `coverage_uniformity`,
      `coverage_uniformity_min`, `coverage_uniformity_max`,
      `expected_relative_matches`, and `detected_relative_matches`.

    MultiQC computes the Hybrid PASS/FAIL result. Strict `<` comparisons are
    used for contamination and short-read target low coverage. Strict `>`
    comparisons are used for short-read coverage, long-read coverage,
    long-read target 10x coverage, and callable target SNVs. Uniformity bounds
    are inclusive. Relative-match counts must be equal. Overall PASS requires
    all nine checks to pass, including the reported versus observed gender
    check.
    """

    def __init__(self):
        super().__init__(
            name="Snakemake Specimens / Samples / Libraries / Inputs / Analysis Units",
            anchor="snakemake-samples",
            href="https://snakemake.readthedocs.io/",
            info=(
                "Reports exact DayOA specimen, sample, physical-library, sequencing-input, "
                "analysis-unit, and ordered input-selection manifests."
            ),
            doi="10.1093/bioinformatics/bts480",
        )

        self.specimen_fields, raw_specimens, specimen_files = self._collect_manifest(
            "snakemake_samples/specimens", "specimens", parse_specimens
        )
        self.sample_fields, raw_samples, sample_files = self._collect_manifest(
            "snakemake_samples/samples", "samples", parse_samples
        )
        self.library_fields, raw_libraries, library_files = self._collect_manifest(
            "snakemake_samples/libraries", "libraries", parse_libraries
        )
        self.sequencing_input_fields, raw_sequencing_inputs, sequencing_input_files = self._collect_manifest(
            "snakemake_samples/sequencing_inputs", "sequencing inputs", parse_sequencing_inputs
        )
        self.analysis_unit_fields, raw_analysis_units, analysis_unit_files = self._collect_manifest(
            "snakemake_samples/analysis_units", "analysis units", parse_analysis_units
        )
        self.analysis_unit_input_fields, raw_analysis_unit_inputs, analysis_unit_input_files = self._collect_manifest(
            "snakemake_samples/analysis_unit_inputs", "analysis unit inputs", parse_analysis_unit_inputs
        )
        self.gender_fields, raw_gender, gender_files = self._collect_identical_files(
            "snakemake_samples/gender_checks", "gender check", parse_gender_checks
        )
        self.hybrid_fields, parsed_hybrid, hybrid_files = self._collect_hybrid_files()
        manifest_files = (
            specimen_files,
            sample_files,
            library_files,
            sequencing_input_files,
            analysis_unit_files,
            analysis_unit_input_files,
        )
        if not any((*manifest_files, gender_files, hybrid_files)):
            raise ModuleNoSamplesFound
        missing_manifests = [
            label
            for label, files in (
                ("specimens.tsv", specimen_files),
                ("samples.tsv", sample_files),
                ("libraries.tsv", library_files),
                ("sequencing_inputs.tsv", sequencing_input_files),
                ("analysis_units.tsv", analysis_unit_files),
                ("analysis_unit_inputs.tsv", analysis_unit_input_files),
            )
            if not files
        ]
        if missing_manifests:
            raise ValueError(
                "Snakemake manifest reporting requires the complete DayOA 13 six-manifest set; missing: "
                + ", ".join(missing_manifests)
            )

        self.input_provenance = {
            "specimens": self._manifest_provenance(specimen_files, raw_specimens),
            "samples": self._manifest_provenance(sample_files, raw_samples),
            "libraries": self._manifest_provenance(library_files, raw_libraries),
            "sequencing_inputs": self._manifest_provenance(sequencing_input_files, raw_sequencing_inputs),
            "analysis_units": self._manifest_provenance(analysis_unit_files, raw_analysis_units),
            "analysis_unit_inputs": self._manifest_provenance(analysis_unit_input_files, raw_analysis_unit_inputs),
            "gender_checks": {"source_paths": sorted(self._source_path(source) for source in gender_files)},
            "hybrid_qc": {"source_paths": sorted(self._source_path(source) for source in hybrid_files)},
        }
        validate_manifest_lineage(
            raw_specimens,
            raw_samples,
            raw_libraries,
            raw_sequencing_inputs,
            raw_analysis_units,
            raw_analysis_unit_inputs,
        )
        resolved_analysis_units = resolve_analysis_units(
            raw_analysis_units,
            raw_libraries,
            raw_sequencing_inputs,
            raw_analysis_unit_inputs,
        )
        self._add_sources(specimen_files[0], raw_specimens, "specimens")
        self._add_sources(sample_files[0], raw_samples, "samples")
        self._add_sources(library_files[0], raw_libraries, "libraries")
        self._add_sources(sequencing_input_files[0], raw_sequencing_inputs, "sequencing_inputs")
        self._add_sources(analysis_unit_files[0], raw_analysis_units, "analysis_units")
        self._add_sources(analysis_unit_input_files[0], raw_analysis_unit_inputs, "analysis_unit_inputs")

        if gender_files:
            validate_gender_samples(raw_specimens, raw_samples, raw_gender)
            self._add_sources(gender_files[0], raw_gender, "gender_checks")

        raw_hybrid: Dict[str, Dict[str, Value]] = {}
        if hybrid_files:
            if not gender_files:
                raise ValueError(
                    "hybrid_seq_batch_qc.tsv requires the six manifests and reported_vs_inferred_sex_check_mqc.tsv"
                )
            raw_hybrid = evaluate_hybrid_qc(
                parsed_hybrid,
                raw_analysis_units,
                raw_specimens,
                raw_samples,
                raw_gender,
            )
            self._add_sources(hybrid_files[0], raw_hybrid, "hybrid_qc")

        self.specimens_data = self.ignore_samples(raw_specimens)
        self.samples_data = self.ignore_samples(raw_samples)
        self.libraries_data = self.ignore_samples(raw_libraries)
        self.sequencing_inputs_data = self.ignore_samples(raw_sequencing_inputs)
        self.analysis_units_data = self.ignore_samples(resolved_analysis_units)
        self.analysis_unit_inputs_data = self.ignore_samples(raw_analysis_unit_inputs)
        self.gender_data = self.ignore_samples(raw_gender)
        self.hybrid_data = self.ignore_samples(raw_hybrid)
        if not any(
            (
                self.specimens_data,
                self.samples_data,
                self.libraries_data,
                self.sequencing_inputs_data,
                self.analysis_units_data,
                self.analysis_unit_inputs_data,
                self.gender_data,
                self.hybrid_data,
            )
        ):
            raise ModuleNoSamplesFound

        log.info(
            "Found %d specimens, %d samples, %d libraries, %d sequencing inputs, "
            "%d analysis units, %d analysis-unit input links, %d gender checks, "
            "and %d Hybrid Seq QC rows",
            len(self.specimens_data),
            len(self.samples_data),
            len(self.libraries_data),
            len(self.sequencing_inputs_data),
            len(self.analysis_units_data),
            len(self.analysis_unit_inputs_data),
            len(self.gender_data),
            len(self.hybrid_data),
        )
        self.add_software_version(None)
        self._add_general_stats()
        self._add_sections()

        if self.specimens_data:
            self.write_data_file(self.specimens_data, "multiqc_snakemake_specimens")
        if self.samples_data:
            self.write_data_file(self.samples_data, "multiqc_snakemake_samples")
        if self.libraries_data:
            self.write_data_file(self.libraries_data, "multiqc_snakemake_libraries")
        if self.sequencing_inputs_data:
            self.write_data_file(self.sequencing_inputs_data, "multiqc_snakemake_sequencing_inputs")
        if self.analysis_units_data:
            self.write_data_file(self.analysis_units_data, "multiqc_snakemake_analysis_units")
        if self.analysis_unit_inputs_data:
            self.write_data_file(
                self.analysis_unit_inputs_data,
                "multiqc_snakemake_analysis_unit_inputs",
            )
        if self.gender_data:
            self.write_data_file(self.gender_data, "multiqc_snakemake_gender_checks")
        if self.hybrid_data:
            self.write_data_file(self.hybrid_data, "multiqc_hybrid_seq_batch_qc")
        self.write_data_file(self.input_provenance, "multiqc_snakemake_samples_input_provenance")

    def _collect_manifest(
        self,
        search_key: str,
        label: str,
        parser: Callable[[Optional[str], str], Tuple[List[str], Dict[str, Dict[str, str]]]],
    ) -> Tuple[List[str], Dict[str, Dict[str, str]], List[LoadedFileDict[str]]]:
        files = list(self.find_log_files(search_key))
        fields: List[str] = []
        canonical: Optional[Dict[str, Dict[str, str]]] = None
        accepted: List[LoadedFileDict[str]] = []
        for source in files:
            parsed_fields, parsed = parser(source["f"], source["fn"])
            if canonical is not None and parsed != canonical:
                paths = sorted([*(self._source_path(item) for item in accepted), self._source_path(source)])
                raise ValueError(f"Conflicting normalized {label} inputs: {', '.join(paths)}")
            if canonical is None:
                fields = parsed_fields
                canonical = parsed
            accepted.append(source)
        return fields, canonical or {}, accepted

    def _collect_identical_files(
        self,
        search_key: str,
        label: str,
        parser: Callable[[Optional[str], str], Tuple[List[str], Dict[str, Dict[str, str]]]],
    ) -> Tuple[List[str], Dict[str, Dict[str, str]], List[LoadedFileDict[str]]]:
        files = list(self.find_log_files(search_key))
        fields: List[str] = []
        canonical: Optional[Dict[str, Dict[str, str]]] = None
        accepted: List[LoadedFileDict[str]] = []
        for source in files:
            parsed_fields, parsed = parser(source["f"], source["fn"])
            if canonical is not None and parsed != canonical:
                paths = sorted([*(self._source_path(item) for item in accepted), self._source_path(source)])
                raise ValueError(f"Conflicting normalized {label} inputs: {', '.join(paths)}")
            if canonical is None:
                fields = parsed_fields
                canonical = parsed
            accepted.append(source)
        return fields, canonical or {}, accepted

    def _collect_hybrid_files(
        self,
    ) -> Tuple[List[str], Dict[str, Dict[str, Value]], List[LoadedFileDict[str]]]:
        files = list(self.find_log_files("snakemake_samples/hybrid_qc"))
        fields: List[str] = []
        canonical: Optional[Dict[str, Dict[str, Value]]] = None
        accepted: List[LoadedFileDict[str]] = []
        for source in files:
            parsed_fields, parsed = parse_hybrid_qc(source["f"], source["fn"])
            if canonical is not None and parsed != canonical:
                paths = sorted([*(self._source_path(item) for item in accepted), self._source_path(source)])
                raise ValueError(f"Conflicting normalized Hybrid Seq Batch QC inputs: {', '.join(paths)}")
            if canonical is None:
                fields = parsed_fields
                canonical = parsed
            accepted.append(source)
        return fields, canonical or {}, accepted

    @staticmethod
    def _source_path(file_obj: Mapping[str, object]) -> str:
        return os.path.join(str(file_obj.get("root", "")), str(file_obj.get("fn", "")))

    @classmethod
    def _manifest_provenance(
        cls, files: List[LoadedFileDict[str]], rows: Mapping[str, Mapping[str, str]]
    ) -> Dict[str, object]:
        canonical_json = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "source_paths": sorted(cls._source_path(source) for source in files),
            "source_file_count": len(files),
            "source_row_counts": [len(rows) for _source in files],
            "normalized_row_count": len(rows),
            "normalized_keys": sorted(rows),
            "normalized_rows_sha256": hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
            "reconciliation_status": "exact",
        }

    def _add_sources(
        self, file_obj: LoadedFileDict[str], rows: Mapping[str, Mapping[str, Value]], section: str
    ) -> None:
        for sample_name in rows:
            self.add_data_source(file_obj, s_name=sample_name, section=section)

    def _add_general_stats(self) -> None:
        if not self.hybrid_data:
            return
        headers: Dict[str, ColumnDict] = {
            "overall_status": {
                "title": "Hybrid QC",
                "description": "Overall Hybrid Seq Batch QC status. PASS requires all nine checks.",
                "bgcols": STATUS_COLORS,
            },
            "failed_checks": {
                "title": "Hybrid Fails",
                "description": "Number of failed Hybrid Seq Batch QC checks",
                "min": 0,
                "scale": "Reds",
            },
            "contamination_estimate_pct": {
                "title": "Contam",
                "description": "Estimated contamination percentage",
                "suffix": "%",
                "min": 0,
                "max": 100,
                "scale": "RdYlGn-rev",
            },
            "long_read_mean_coverage": {
                "title": "LR Cov",
                "description": "Long-read mean coverage",
                "suffix": "x",
                "min": 0,
                "scale": "RdYlGn",
            },
            "hybrid_callable_target_snvs_pct": {
                "title": "Hybrid Callable",
                "description": "Callable hybrid SNVs in the target region",
                "suffix": "%",
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
        }
        configured_headers = self.get_general_stats_headers(all_headers=headers)
        if configured_headers:
            self.general_stats_addcols(
                self.hybrid_data,
                configured_headers,
                namespace="Snakemake Manifest Lineage",
            )

    def _add_sections(self) -> None:
        if self.specimens_data:
            self.add_section(
                name="Specimens",
                anchor="snakemake-samples-specimens",
                description="Source-faithful rows from <code>specimens.tsv</code>, keyed by exact <code>SPECIMEN_ID</code>.",
                plot=table.plot(
                    self.specimens_data,
                    table_headers(self.specimens_data),
                    {
                        "id": "snakemake_specimens_table",
                        "title": "Snakemake Specimens / Samples / Libraries: Specimens",
                        "no_violin": True,
                    },
                ),
            )
        if self.samples_data:
            self.add_section(
                name="Samples",
                anchor="snakemake-samples-samples",
                description=(
                    "Source-faithful rows from <code>samples.tsv</code>, keyed by exact <code>SAMPLEID</code> "
                    "and retaining the <code>SPECIMEN_ID</code> parent."
                ),
                plot=table.plot(
                    self.samples_data,
                    table_headers(self.samples_data),
                    {
                        "id": "snakemake_samples_table",
                        "title": "Snakemake Specimens / Samples / Libraries: Samples",
                        "no_violin": True,
                    },
                ),
            )
        if self.libraries_data:
            self.add_section(
                name="Libraries",
                anchor="snakemake-samples-libraries",
                description=(
                    "Source-faithful physical-library rows from <code>libraries.tsv</code>, keyed by exact "
                    "<code>LIBRARY_ID</code> and retaining the <code>SAMPLEID</code> parent."
                ),
                plot=table.plot(
                    self.libraries_data,
                    table_headers(self.libraries_data),
                    {
                        "id": "snakemake_libraries_table",
                        "title": "Snakemake Manifest Lineage: Physical Libraries",
                        "no_violin": True,
                    },
                ),
            )
        if self.sequencing_inputs_data:
            self.add_section(
                name="Sequencing Inputs",
                anchor="snakemake-samples-sequencing-inputs",
                description=(
                    "Source-faithful rows from <code>sequencing_inputs.tsv</code>, keyed by exact "
                    "<code>SEQUENCING_INPUT_UID</code>. <code>MODALITY</code> and <code>LAYOUT</code> "
                    "are displayed exactly as supplied."
                ),
                plot=table.plot(
                    self.sequencing_inputs_data,
                    table_headers(self.sequencing_inputs_data),
                    {
                        "id": "snakemake_sequencing_inputs_table",
                        "title": "Snakemake Manifest Lineage: Sequencing Inputs",
                        "no_violin": True,
                    },
                ),
            )
        if self.analysis_units_data:
            self.add_section(
                name="Analysis Units and Resolved Inputs",
                anchor="snakemake-samples-analysis-units",
                description=(
                    "Rows from <code>analysis_units.tsv</code>, keyed by exact "
                    "<code>ANALYSIS_UNIT_UID</code>. Selected library, sequencing-input, role, ordinal, "
                    "modality, and layout arrays are resolved only from the required join."
                ),
                plot=table.plot(
                    self.analysis_units_data,
                    table_headers(self.analysis_units_data),
                    {
                        "id": "snakemake_analysis_units_table",
                        "title": "Snakemake Manifest Lineage: Analysis Units",
                        "no_violin": True,
                    },
                ),
            )
        if self.analysis_unit_inputs_data:
            self.add_section(
                name="Analysis Unit Input Topology",
                anchor="snakemake-samples-analysis-unit-inputs",
                description=("Source-faithful ordered many-to-many rows from <code>analysis_unit_inputs.tsv</code>."),
                plot=table.plot(
                    self.analysis_unit_inputs_data,
                    table_headers(self.analysis_unit_inputs_data),
                    {
                        "id": "snakemake_analysis_unit_inputs_table",
                        "title": "Snakemake Manifest Lineage: Analysis Unit Inputs",
                        "no_violin": True,
                    },
                ),
            )
        if self.gender_data:
            self.add_section(
                name="Reported and Observed Gender Checks",
                anchor="snakemake-samples-gender-checks",
                description=(
                    "Reported <code>BIOLOGICAL_SEX</code> provenance from <code>specimens.tsv</code> compared with "
                    "the observed inferred sex-chromosome complement. Non-evaluable evidence is not a pass."
                ),
                plot=table.plot(
                    self.gender_data,
                    gender_headers(self.gender_data),
                    {
                        "id": "snakemake_gender_checks_table",
                        "title": "Reported and Observed Gender Checks",
                        "no_violin": True,
                    },
                ),
            )
        if self.hybrid_data:
            self.add_section(
                name="Hybrid Seq Batch QC",
                anchor="snakemake-samples-hybrid-seq-batch-qc",
                description=(
                    "Per-analysis-unit PASS/FAIL evaluation computed from "
                    "<code>hybrid_seq_batch_qc.tsv</code>. "
                    "Overall PASS requires all nine checks to pass."
                ),
                plot=table.plot(
                    self.hybrid_data,
                    hybrid_headers(self.hybrid_data),
                    {"id": "hybrid_seq_batch_qc_table", "title": "Hybrid Seq Batch QC", "no_violin": True},
                ),
            )


def table_headers(rows: Mapping[str, Mapping[str, Value]]) -> Dict[str, ColumnDict]:
    headers: Dict[str, ColumnDict] = {}
    for row in rows.values():
        for key in row:
            headers.setdefault(key, {"title": pretty_name(key)})
    return headers


def gender_headers(rows: Mapping[str, Mapping[str, Value]]) -> Dict[str, ColumnDict]:
    headers = table_headers(rows)
    if "comparison_status" in headers:
        headers["comparison_status"].update({"title": "Comparison Status", "bgcols": STATUS_COLORS})
    if "comparison_pass" in headers:
        headers["comparison_pass"].update(
            {"title": "Comparison Pass", "bgcols": {"true": "#d1e7dd", "false": "#f8d7da"}}
        )
    if "inferred_sex_chromosome_complement" in headers:
        headers["inferred_sex_chromosome_complement"]["title"] = "Observed Complement"
    return headers


def hybrid_headers(rows: Mapping[str, Mapping[str, Value]]) -> Dict[str, ColumnDict]:
    headers = table_headers(rows)
    status_columns = ["overall_status", "gender_check"] + [
        column for column in next(iter(rows.values())) if column.endswith("_check")
    ]
    for column in status_columns:
        if column in headers:
            headers[column].update({"bgcols": STATUS_COLORS})
    headers["overall_status"]["title"] = "Overall QC"
    headers["failed_checks"].update({"title": "Failed Checks", "scale": "Reds", "min": 0})
    for column in HYBRID_REQUIRED_COLUMNS:
        if column in headers and "_pct" in column:
            headers[column].update({"suffix": "%", "min": 0, "max": 100})
    return headers


def pretty_name(value: str) -> str:
    replacements = {
        "qc": "QC",
        "snv": "SNV",
        "snvs": "SNVs",
        "sr": "SR",
        "lr": "LR",
        "pct": "%",
        "10x": "10x",
        "id": "ID",
        "uid": "UID",
    }
    words = value.replace("_", " ").split()
    return " ".join(replacements.get(word.lower(), word.capitalize()) for word in words)
