import csv
import math
from io import StringIO
from typing import Dict, List, Mapping, Optional, Tuple, Union


Numeric = Union[int, float]
Value = Union[int, float, str, bool]

GENDER_REQUIRED_COLUMNS = frozenset(
    {
        "Sample",
        "reported_sex_raw",
        "inferred_sex_chromosome_complement",
        "comparison_status",
        "comparison_pass",
    }
)

HYBRID_SCHEMA_VERSION = "1"
HYBRID_REQUIRED_COLUMNS = (
    "schema_version",
    "analysis_unit_uid",
    "sample_id",
    "contamination_estimate_pct",
    "contamination_max_pct",
    "short_read_coverage_threshold",
    "short_read_bases_above_threshold_pct",
    "short_read_bases_above_threshold_pct_min",
    "long_read_mean_coverage",
    "long_read_mean_coverage_min",
    "long_read_target_10x_pct",
    "long_read_target_10x_pct_min",
    "short_read_target_coverage_threshold",
    "short_read_target_below_threshold_pct",
    "short_read_target_below_threshold_pct_max",
    "hybrid_callable_target_snvs_pct",
    "hybrid_callable_target_snvs_pct_min",
    "coverage_uniformity",
    "coverage_uniformity_min",
    "coverage_uniformity_max",
    "expected_relative_matches",
    "detected_relative_matches",
)

PERCENT_COLUMNS = frozenset(
    {
        "contamination_estimate_pct",
        "contamination_max_pct",
        "short_read_bases_above_threshold_pct",
        "short_read_bases_above_threshold_pct_min",
        "long_read_target_10x_pct",
        "long_read_target_10x_pct_min",
        "short_read_target_below_threshold_pct",
        "short_read_target_below_threshold_pct_max",
        "hybrid_callable_target_snvs_pct",
        "hybrid_callable_target_snvs_pct_min",
    }
)

NONNEGATIVE_FLOAT_COLUMNS = frozenset(
    {
        "short_read_coverage_threshold",
        "long_read_mean_coverage",
        "long_read_mean_coverage_min",
        "short_read_target_coverage_threshold",
        "coverage_uniformity",
        "coverage_uniformity_min",
        "coverage_uniformity_max",
    }
)

INTEGER_COLUMNS = frozenset({"expected_relative_matches", "detected_relative_matches"})
STAGED_SAMPLE_METADATA_COLUMNS = frozenset({"Sample", "input_origin"})
VALID_STAGED_LIBRARY_ORIGINS = frozenset({"input_manifest", "generated_by_snakemake"})


def parse_tsv(text: Optional[str], filename: str, label: str) -> Tuple[List[str], List[Dict[str, str]]]:
    if text is None:
        raise ValueError(f"Could not read {label} TSV: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if not reader.fieldnames:
        raise ValueError(f"{label} TSV has no header: {filename}")
    fieldnames = list(reader.fieldnames)
    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError(f"{label} TSV has duplicate column names: {filename}")

    rows: List[Dict[str, str]] = []
    for line_number, raw_row in enumerate(reader, start=2):
        if None in raw_row:
            raise ValueError(f"{label} TSV line {line_number} has more fields than its header: {filename}")
        missing = [column for column in fieldnames if raw_row[column] is None]
        if missing:
            raise ValueError(f"{label} TSV line {line_number} has fewer fields than its header: {filename}")
        rows.append({column: str(raw_row[column]) for column in fieldnames})
    if not rows:
        raise ValueError(f"{label} TSV has no data rows: {filename}")
    return fieldnames, rows


def parse_specimens(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "specimens")
    if "SPECIMEN_ID" not in fieldnames:
        raise ValueError(f"specimens.tsv is missing required SPECIMEN_ID column: {filename}")
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        specimen_id = row["SPECIMEN_ID"].strip()
        if not specimen_id:
            raise ValueError(f"specimens.tsv line {line_number} has a blank SPECIMEN_ID: {filename}")
        if specimen_id in parsed:
            raise ValueError(f"specimens.tsv contains duplicate SPECIMEN_ID '{specimen_id}': {filename}")
        parsed[specimen_id] = row
    return fieldnames, parsed


def parse_samples(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "samples")
    missing = sorted({"SAMPLEID", "SPECIMEN_ID"} - set(fieldnames))
    if missing:
        raise ValueError(f"samples.tsv is missing required column(s) {', '.join(missing)}: {filename}")
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_id = row["SAMPLEID"].strip()
        if not sample_id:
            raise ValueError(f"samples.tsv line {line_number} has a blank SAMPLEID: {filename}")
        if sample_id in parsed:
            raise ValueError(f"samples.tsv contains duplicate SAMPLEID '{sample_id}': {filename}")
        parsed[sample_id] = row
    return fieldnames, parsed


def _parse_staged_entity(
    text: Optional[str],
    filename: str,
    *,
    label: str,
    key_field: str,
    valid_origins: frozenset[str],
) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, f"staged {label}")
    required = {"Sample", "input_origin", key_field}
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"staged {label} TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_key = row["Sample"].strip()
        entity_id = row[key_field].strip()
        if not sample_key or sample_key != entity_id:
            raise ValueError(
                f"staged {label} TSV Sample must exactly match {key_field} on line {line_number}: {filename}"
            )
        origin = row["input_origin"].strip()
        if origin not in valid_origins:
            allowed = ", ".join(sorted(valid_origins))
            raise ValueError(
                f"staged {label} TSV input_origin must be one of {allowed} on line {line_number}: {filename}"
            )
        if entity_id in parsed:
            raise ValueError(f"staged {label} TSV contains duplicate Sample '{entity_id}': {filename}")
        parsed[entity_id] = {
            column: row[column] for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS
        }
    return [column for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS], parsed


def parse_staged_specimens(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_staged_entity(
        text,
        filename,
        label="specimens",
        key_field="SPECIMEN_ID",
        valid_origins=frozenset({"input_manifest"}),
    )


def parse_staged_samples(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_staged_entity(
        text,
        filename,
        label="samples",
        key_field="SAMPLEID",
        valid_origins=frozenset({"input_manifest"}),
    )


def parse_libraries(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "libraries")
    missing = sorted({"ANALYSIS_UNIT_UID", "SAMPLEID"} - set(fieldnames))
    if missing:
        raise ValueError(f"libraries.tsv is missing required column(s) {', '.join(missing)}: {filename}")
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_id = row["SAMPLEID"].strip()
        if not sample_id:
            raise ValueError(f"libraries.tsv line {line_number} has a blank SAMPLEID: {filename}")
        unit_uid = row["ANALYSIS_UNIT_UID"].strip()
        if not unit_uid:
            raise ValueError(f"libraries.tsv line {line_number} has a blank ANALYSIS_UNIT_UID: {filename}")
        if unit_uid in parsed:
            raise ValueError(f"libraries.tsv contains duplicate ANALYSIS_UNIT_UID '{unit_uid}': {filename}")
        parsed[unit_uid] = row
    output_fields = list(fieldnames)
    return output_fields, parsed


def parse_staged_libraries(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "staged libraries")
    required = {"Sample", "input_origin", "ANALYSIS_UNIT_UID", "SAMPLEID"}
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"staged libraries TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        unit_uid = row["ANALYSIS_UNIT_UID"].strip()
        sample_key = row["Sample"].strip()
        if not sample_key or sample_key != unit_uid:
            raise ValueError(
                f"staged libraries TSV Sample must exactly match ANALYSIS_UNIT_UID on line {line_number}: {filename}"
            )
        if row["input_origin"].strip() not in VALID_STAGED_LIBRARY_ORIGINS:
            allowed = ", ".join(sorted(VALID_STAGED_LIBRARY_ORIGINS))
            raise ValueError(
                f"staged libraries TSV input_origin must be one of {allowed} on line {line_number}: {filename}"
            )
        if unit_uid in parsed:
            raise ValueError(f"staged libraries TSV contains duplicate Sample '{unit_uid}': {filename}")
        source_row = {column: row[column] for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS}
        parsed[unit_uid] = source_row
    output_fields = [column for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS]
    return output_fields, parsed


def validate_manifest_lineage(
    specimens: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    libraries: Mapping[str, Mapping[str, str]],
) -> None:
    unknown_specimens = sorted({row["SPECIMEN_ID"].strip() for row in samples.values()} - set(specimens))
    if unknown_specimens:
        raise ValueError(
            "samples.tsv references SPECIMEN_ID values absent from specimens.tsv: " + ", ".join(unknown_specimens)
        )
    unknown_samples = sorted({row["SAMPLEID"].strip() for row in libraries.values()} - set(samples))
    if unknown_samples:
        raise ValueError(
            "libraries.tsv references SAMPLEID values absent from samples.tsv: " + ", ".join(unknown_samples)
        )


def parse_gender_checks(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "reported versus observed gender check")
    missing = sorted(GENDER_REQUIRED_COLUMNS - set(fieldnames))
    if missing:
        raise ValueError(f"gender check TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_id = row["Sample"].strip()
        if not sample_id:
            raise ValueError(f"gender check TSV line {line_number} has a blank Sample: {filename}")
        if sample_id in parsed:
            raise ValueError(f"gender check TSV contains duplicate Sample '{sample_id}': {filename}")
        comparison_pass = row["comparison_pass"].strip().lower()
        comparison_status = row["comparison_status"].strip()
        if comparison_pass not in {"", "true", "false"}:
            raise ValueError(
                f"gender check TSV has invalid comparison_pass '{row['comparison_pass']}' for {sample_id}: {filename}"
            )
        if comparison_status == "PASS" and comparison_pass != "true":
            raise ValueError(f"gender check PASS row must set comparison_pass=true for {sample_id}: {filename}")
        if comparison_status == "FAIL" and comparison_pass != "false":
            raise ValueError(f"gender check FAIL row must set comparison_pass=false for {sample_id}: {filename}")
        parsed[sample_id] = {key: value for key, value in row.items() if key != "Sample"}
    return fieldnames, parsed


def validate_gender_samples(
    specimens: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    gender_checks: Mapping[str, Mapping[str, str]],
) -> None:
    if any("BIOLOGICAL_SEX" not in row for row in specimens.values()):
        raise ValueError("specimens.tsv must contain BIOLOGICAL_SEX when gender checks are present")
    missing = sorted(set(samples) - set(gender_checks))
    unknown = sorted(set(gender_checks) - set(samples))
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing check rows: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown check rows: {', '.join(unknown)}")
        raise ValueError("gender check rows must exactly match samples.tsv; " + "; ".join(parts))
    mismatched = sorted(
        sample_id
        for sample_id, row in gender_checks.items()
        if row["reported_sex_raw"].strip()
        != specimens[samples[sample_id]["SPECIMEN_ID"].strip()]["BIOLOGICAL_SEX"].strip()
    )
    if mismatched:
        raise ValueError(
            "gender check reported_sex_raw does not match specimens.tsv BIOLOGICAL_SEX for: " + ", ".join(mismatched)
        )


def _parse_float(value: str, column: str, unit_uid: str, filename: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Hybrid QC {column} must be numeric for {unit_uid}: {filename}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"Hybrid QC {column} must be finite for {unit_uid}: {filename}")
    return parsed


def _parse_nonnegative_integer(value: str, column: str, unit_uid: str, filename: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Hybrid QC {column} must be an integer for {unit_uid}: {filename}") from exc
    if parsed < 0:
        raise ValueError(f"Hybrid QC {column} must be nonnegative for {unit_uid}: {filename}")
    return parsed


def _number(row: Mapping[str, Value], column: str) -> Numeric:
    value = row[column]
    if not isinstance(value, (int, float)):
        raise TypeError(f"Hybrid QC evaluated column is not numeric: {column}")
    return value


def parse_hybrid_qc(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, Value]]]:
    fieldnames, rows = parse_tsv(text, filename, "Hybrid Seq Batch QC")
    missing = sorted(set(HYBRID_REQUIRED_COLUMNS) - set(fieldnames))
    if missing:
        raise ValueError(f"Hybrid QC TSV is missing required column(s) {', '.join(missing)}: {filename}")
    unexpected = sorted(set(fieldnames) - set(HYBRID_REQUIRED_COLUMNS))
    if unexpected:
        raise ValueError(f"Hybrid QC TSV has unexpected column(s) {', '.join(unexpected)}: {filename}")
    if tuple(fieldnames) != HYBRID_REQUIRED_COLUMNS:
        raise ValueError(f"Hybrid QC TSV columns are not in the required schema order: {filename}")

    parsed: Dict[str, Dict[str, Value]] = {}
    for line_number, row in enumerate(rows, start=2):
        unit_uid = row["analysis_unit_uid"].strip()
        sample_id = row["sample_id"].strip()
        if row["schema_version"].strip() != HYBRID_SCHEMA_VERSION:
            raise ValueError(
                f"Hybrid QC line {line_number} requires schema_version {HYBRID_SCHEMA_VERSION}: {filename}"
            )
        if not unit_uid or not sample_id:
            raise ValueError(f"Hybrid QC line {line_number} has a blank analysis_unit_uid or sample_id: {filename}")
        if unit_uid in parsed:
            raise ValueError(f"Hybrid QC TSV contains duplicate analysis_unit_uid '{unit_uid}': {filename}")

        typed_row: Dict[str, Value] = dict(row)
        for column in PERCENT_COLUMNS:
            value = _parse_float(row[column], column, unit_uid, filename)
            if not 0 <= value <= 100:
                raise ValueError(f"Hybrid QC {column} must be between 0 and 100 for {unit_uid}: {filename}")
            typed_row[column] = value
        for column in NONNEGATIVE_FLOAT_COLUMNS:
            value = _parse_float(row[column], column, unit_uid, filename)
            if value < 0:
                raise ValueError(f"Hybrid QC {column} must be nonnegative for {unit_uid}: {filename}")
            typed_row[column] = value
        for column in INTEGER_COLUMNS:
            typed_row[column] = _parse_nonnegative_integer(row[column], column, unit_uid, filename)
        if _number(typed_row, "coverage_uniformity_min") > _number(typed_row, "coverage_uniformity_max"):
            raise ValueError(f"Hybrid QC uniformity minimum exceeds maximum for {unit_uid}: {filename}")
        parsed[unit_uid] = typed_row
    return fieldnames, parsed


def evaluate_hybrid_qc(
    hybrid_rows: Mapping[str, Mapping[str, Value]],
    libraries: Mapping[str, Mapping[str, str]],
    specimens: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    gender_checks: Mapping[str, Mapping[str, str]],
) -> Dict[str, Dict[str, Value]]:
    missing = sorted(set(libraries) - set(hybrid_rows))
    unknown = sorted(set(hybrid_rows) - set(libraries))
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing libraries: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown libraries: {', '.join(unknown)}")
        raise ValueError("Hybrid QC rows must exactly match libraries.tsv; " + "; ".join(parts))

    evaluated: Dict[str, Dict[str, Value]] = {}
    for unit_uid, row in hybrid_rows.items():
        sample_id = str(row["sample_id"])
        unit_sample_id = libraries[unit_uid]["SAMPLEID"].strip()
        if sample_id != unit_sample_id:
            raise ValueError(
                f"Hybrid QC sample_id '{sample_id}' does not match libraries.tsv SAMPLEID '{unit_sample_id}' for {unit_uid}"
            )
        gender = gender_checks[sample_id]
        checks = {
            "gender_check": gender["comparison_status"] == "PASS" and gender["comparison_pass"].lower() == "true",
            "contamination_check": _number(row, "contamination_estimate_pct") < _number(row, "contamination_max_pct"),
            "short_read_coverage_check": _number(row, "short_read_bases_above_threshold_pct")
            > _number(row, "short_read_bases_above_threshold_pct_min"),
            "long_read_coverage_check": _number(row, "long_read_mean_coverage")
            > _number(row, "long_read_mean_coverage_min"),
            "long_read_target_10x_check": _number(row, "long_read_target_10x_pct")
            > _number(row, "long_read_target_10x_pct_min"),
            "short_read_target_low_coverage_check": _number(row, "short_read_target_below_threshold_pct")
            < _number(row, "short_read_target_below_threshold_pct_max"),
            "hybrid_callable_snvs_check": _number(row, "hybrid_callable_target_snvs_pct")
            > _number(row, "hybrid_callable_target_snvs_pct_min"),
            "uniformity_check": _number(row, "coverage_uniformity_min")
            <= _number(row, "coverage_uniformity")
            <= _number(row, "coverage_uniformity_max"),
            "relative_matches_check": _number(row, "expected_relative_matches")
            == _number(row, "detected_relative_matches"),
        }
        check_statuses = {key: "PASS" if passed else "FAIL" for key, passed in checks.items()}
        failed_checks = sum(not passed for passed in checks.values())
        evaluated[unit_uid] = {
            "sample_id": sample_id,
            "reported_gender": specimens[samples[sample_id]["SPECIMEN_ID"]]["BIOLOGICAL_SEX"],
            "observed_gender": gender["inferred_sex_chromosome_complement"],
            "overall_status": "PASS" if failed_checks == 0 else "FAIL",
            "failed_checks": failed_checks,
            **check_statuses,
            **row,
        }
    return evaluated
