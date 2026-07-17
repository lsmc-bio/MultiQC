import csv
import math
import re
from io import StringIO
from typing import Dict, List, Mapping, Optional, Tuple, Union


Numeric = Union[int, float]
Value = Union[int, float, str, bool]

UNIT_UID_COLUMNS = (
    "RUNID",
    "SAMPLEID",
    "EXPERIMENTID",
    "LANEID",
    "BARCODEID",
    "LIBPREP",
    "SEQ_VENDOR",
    "SEQ_PLATFORM",
)
UNIT_UID_REQUIRED_COLUMNS = frozenset(UNIT_UID_COLUMNS) - {"SEQ_VENDOR"}

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
VALID_STAGED_UNIT_ORIGINS = frozenset({"input_manifest", "generated_by_snakemake"})


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


def parse_samples(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "samples")
    if "SAMPLEID" not in fieldnames:
        raise ValueError(f"samples.tsv is missing required SAMPLEID column: {filename}")
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_id = row["SAMPLEID"].strip()
        if not sample_id:
            raise ValueError(f"samples.tsv line {line_number} has a blank SAMPLEID: {filename}")
        if sample_id in parsed:
            raise ValueError(f"samples.tsv contains duplicate SAMPLEID '{sample_id}': {filename}")
        parsed[sample_id] = row
    return fieldnames, parsed


def parse_staged_samples(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "staged samples")
    required = {"Sample", "input_origin", "SAMPLEID"}
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"staged samples TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_key = row["Sample"].strip()
        sample_id = row["SAMPLEID"].strip()
        if not sample_key or sample_key != sample_id:
            raise ValueError(f"staged samples TSV Sample must exactly match SAMPLEID on line {line_number}: {filename}")
        if row["input_origin"].strip() != "input_manifest":
            raise ValueError(
                f"staged samples TSV requires input_origin=input_manifest on line {line_number}: {filename}"
            )
        if sample_id in parsed:
            raise ValueError(f"staged samples TSV contains duplicate Sample '{sample_id}': {filename}")
        parsed[sample_id] = {
            column: row[column] for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS
        }
    return [column for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS], parsed


def _clean_uid_component(value: str) -> str:
    text = str(value).strip()
    if text.lower() in {"", "na", "none"}:
        return ""
    return re.sub(r"\s+", "", text)


def analysis_unit_uid(row: Mapping[str, str], filename: str) -> str:
    explicit_values = [
        _clean_uid_component(row[field])
        for field in ("analysis_unit_uid", "ANALYSIS_UNIT_UID")
        if field in row and _clean_uid_component(row[field])
    ]
    if len(set(explicit_values)) > 1:
        raise ValueError(f"units.tsv has conflicting analysis unit identifiers: {filename}")
    if explicit_values:
        return explicit_values[0]

    missing = sorted(UNIT_UID_REQUIRED_COLUMNS - set(row))
    if missing:
        raise ValueError(
            f"units.tsv cannot construct analysis_unit_uid; missing column(s) {', '.join(missing)}: {filename}"
        )
    components = [_clean_uid_component(row.get(column, "")) for column in UNIT_UID_COLUMNS]
    components = [component for component in components if component]
    if not components:
        raise ValueError(f"units.tsv row cannot construct a nonempty analysis_unit_uid: {filename}")
    return "-".join(components)


def parse_units(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "units")
    if "SAMPLEID" not in fieldnames:
        raise ValueError(f"units.tsv is missing required SAMPLEID column: {filename}")
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        sample_id = row["SAMPLEID"].strip()
        if not sample_id:
            raise ValueError(f"units.tsv line {line_number} has a blank SAMPLEID: {filename}")
        unit_uid = analysis_unit_uid(row, filename)
        if unit_uid in parsed:
            raise ValueError(f"units.tsv contains duplicate analysis_unit_uid '{unit_uid}': {filename}")
        parsed[unit_uid] = {**row, "analysis_unit_uid": unit_uid}
    output_fields = list(fieldnames)
    if "analysis_unit_uid" not in output_fields:
        output_fields.insert(0, "analysis_unit_uid")
    return output_fields, parsed


def parse_staged_units(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "staged units")
    required = {"Sample", "input_origin", "SAMPLEID"}
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"staged units TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        unit_uid = analysis_unit_uid(row, filename)
        sample_key = row["Sample"].strip()
        if not sample_key or sample_key != unit_uid:
            raise ValueError(
                f"staged units TSV Sample must exactly match analysis_unit_uid on line {line_number}: {filename}"
            )
        if row["input_origin"].strip() not in VALID_STAGED_UNIT_ORIGINS:
            allowed = ", ".join(sorted(VALID_STAGED_UNIT_ORIGINS))
            raise ValueError(
                f"staged units TSV input_origin must be one of {allowed} on line {line_number}: {filename}"
            )
        if unit_uid in parsed:
            raise ValueError(f"staged units TSV contains duplicate Sample '{unit_uid}': {filename}")
        source_row = {column: row[column] for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS}
        parsed[unit_uid] = {**source_row, "analysis_unit_uid": unit_uid}
    output_fields = [column for column in fieldnames if column not in STAGED_SAMPLE_METADATA_COLUMNS]
    if "analysis_unit_uid" not in output_fields:
        output_fields.insert(0, "analysis_unit_uid")
    return output_fields, parsed


def validate_unit_samples(samples: Mapping[str, Mapping[str, str]], units: Mapping[str, Mapping[str, str]]) -> None:
    unknown = sorted({row["SAMPLEID"].strip() for row in units.values()} - set(samples))
    if unknown:
        raise ValueError(f"units.tsv references SAMPLEID values absent from samples.tsv: {', '.join(unknown)}")


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
    samples: Mapping[str, Mapping[str, str]], gender_checks: Mapping[str, Mapping[str, str]]
) -> None:
    if any("BIOLOGICAL_SEX" not in row for row in samples.values()):
        raise ValueError("samples.tsv must contain BIOLOGICAL_SEX when gender checks are present")
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
        if row["reported_sex_raw"].strip() != samples[sample_id]["BIOLOGICAL_SEX"].strip()
    )
    if mismatched:
        raise ValueError(
            "gender check reported_sex_raw does not match samples.tsv BIOLOGICAL_SEX for: " + ", ".join(mismatched)
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
    units: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    gender_checks: Mapping[str, Mapping[str, str]],
) -> Dict[str, Dict[str, Value]]:
    missing = sorted(set(units) - set(hybrid_rows))
    unknown = sorted(set(hybrid_rows) - set(units))
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing units: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown units: {', '.join(unknown)}")
        raise ValueError("Hybrid QC rows must exactly match units.tsv; " + "; ".join(parts))

    evaluated: Dict[str, Dict[str, Value]] = {}
    for unit_uid, row in hybrid_rows.items():
        sample_id = str(row["sample_id"])
        unit_sample_id = units[unit_uid]["SAMPLEID"].strip()
        if sample_id != unit_sample_id:
            raise ValueError(
                f"Hybrid QC sample_id '{sample_id}' does not match units.tsv SAMPLEID '{unit_sample_id}' for {unit_uid}"
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
            "reported_gender": samples[sample_id]["BIOLOGICAL_SEX"],
            "observed_gender": gender["inferred_sex_chromosome_complement"],
            "overall_status": "PASS" if failed_checks == 0 else "FAIL",
            "failed_checks": failed_checks,
            **check_statuses,
            **row,
        }
    return evaluated
