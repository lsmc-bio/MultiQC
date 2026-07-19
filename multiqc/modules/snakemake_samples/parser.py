import csv
import json
import math
from collections import defaultdict
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
ENTITY_KEYS = {
    "specimens": "SPECIMEN_ID",
    "samples": "SAMPLEID",
    "libraries": "LIBRARY_ID",
    "sequencing inputs": "SEQUENCING_INPUT_UID",
    "analysis units": "ANALYSIS_UNIT_UID",
}
ENTITY_REQUIRED_COLUMNS = {
    "specimens": frozenset({"SPECIMEN_ID"}),
    "samples": frozenset({"SAMPLEID", "SPECIMEN_ID"}),
    "libraries": frozenset({"LIBRARY_ID", "SAMPLEID"}),
    "sequencing inputs": frozenset({"SEQUENCING_INPUT_UID", "LIBRARY_ID", "MODALITY", "LAYOUT"}),
    "analysis units": frozenset({"ANALYSIS_UNIT_UID", "SAMPLEID"}),
}
ANALYSIS_UNIT_INPUT_REQUIRED_COLUMNS = frozenset({"ANALYSIS_UNIT_UID", "SEQUENCING_INPUT_UID", "ROLE", "INPUT_ORDINAL"})
INPUT_ROLES = frozenset({"sr", "lr"})
INPUT_LAYOUTS = frozenset({"paired_fastq", "single_fastq", "aligned_bam", "aligned_cram", "vcf"})


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


def _parse_entity(text: Optional[str], filename: str, label: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, label)
    required = ENTITY_REQUIRED_COLUMNS[label]
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"{filename} is missing required column(s) {', '.join(missing)}")
    key_field = ENTITY_KEYS[label]
    parsed: Dict[str, Dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        blank = sorted(column for column in required if not row[column].strip())
        if blank:
            raise ValueError(f"{filename} line {line_number} has blank required column(s) " + ", ".join(blank))
        key = row[key_field].strip()
        if key in parsed:
            raise ValueError(f"{filename} contains duplicate {key_field} '{key}'")
        normalized = dict(row)
        for column in required:
            normalized[column] = normalized[column].strip()
        if label == "sequencing inputs":
            modality = normalized["MODALITY"]
            layout = normalized["LAYOUT"]
            if modality not in INPUT_ROLES:
                raise ValueError(
                    f"{filename} line {line_number} MODALITY must be one of {sorted(INPUT_ROLES)}; "
                    f"observed {modality!r}"
                )
            if layout not in INPUT_LAYOUTS:
                raise ValueError(
                    f"{filename} line {line_number} LAYOUT must be one of {sorted(INPUT_LAYOUTS)}; observed {layout!r}"
                )
        parsed[key] = normalized
    return fieldnames, parsed


def parse_specimens(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_entity(text, filename, "specimens")


def parse_samples(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_entity(text, filename, "samples")


def parse_libraries(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_entity(text, filename, "libraries")


def parse_sequencing_inputs(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_entity(text, filename, "sequencing inputs")


def parse_analysis_units(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    return _parse_entity(text, filename, "analysis units")


def parse_analysis_unit_inputs(text: Optional[str], filename: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    fieldnames, rows = parse_tsv(text, filename, "analysis unit inputs")
    missing = sorted(ANALYSIS_UNIT_INPUT_REQUIRED_COLUMNS - set(fieldnames))
    if missing:
        raise ValueError(f"{filename} is missing required column(s) {', '.join(missing)}")
    parsed: Dict[str, Dict[str, str]] = {}
    observed_order: Dict[str, List[int]] = defaultdict(list)
    observed_inputs: Dict[str, set] = defaultdict(set)
    for line_number, row in enumerate(rows, start=2):
        blank = sorted(column for column in ANALYSIS_UNIT_INPUT_REQUIRED_COLUMNS if not row[column].strip())
        if blank:
            raise ValueError(f"{filename} line {line_number} has blank required column(s) " + ", ".join(blank))
        unit_uid = row["ANALYSIS_UNIT_UID"].strip()
        input_uid = row["SEQUENCING_INPUT_UID"].strip()
        role = row["ROLE"].strip()
        if role not in INPUT_ROLES:
            raise ValueError(
                f"{filename} line {line_number} ROLE must be one of {sorted(INPUT_ROLES)}; observed {role!r}"
            )
        try:
            ordinal = int(row["INPUT_ORDINAL"])
        except ValueError as exc:
            raise ValueError(f"{filename} line {line_number} INPUT_ORDINAL must be a positive integer") from exc
        if ordinal < 1 or str(ordinal) != row["INPUT_ORDINAL"]:
            raise ValueError(f"{filename} line {line_number} INPUT_ORDINAL must be a canonical positive integer")
        if input_uid in observed_inputs[unit_uid]:
            raise ValueError(f"{filename} selects SEQUENCING_INPUT_UID {input_uid!r} more than once for {unit_uid!r}")
        observed_inputs[unit_uid].add(input_uid)
        observed_order[unit_uid].append(ordinal)
        key = f"{unit_uid}|{ordinal}|{input_uid}"
        if key in parsed:
            raise ValueError(f"{filename} contains duplicate link {key!r}")
        normalized = dict(row)
        normalized.update(
            {
                "ANALYSIS_UNIT_UID": unit_uid,
                "SEQUENCING_INPUT_UID": input_uid,
                "ROLE": role,
                "INPUT_ORDINAL": str(ordinal),
            }
        )
        parsed[key] = normalized
    for unit_uid, ordinals in observed_order.items():
        expected = list(range(1, len(ordinals) + 1))
        if ordinals != expected:
            raise ValueError(
                f"{filename} INPUT_ORDINAL values for {unit_uid!r} must be in exact contiguous order; "
                f"observed {ordinals}"
            )
    return fieldnames, parsed


def validate_manifest_lineage(
    specimens: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    libraries: Mapping[str, Mapping[str, str]],
    sequencing_inputs: Mapping[str, Mapping[str, str]],
    analysis_units: Mapping[str, Mapping[str, str]],
    analysis_unit_inputs: Mapping[str, Mapping[str, str]],
) -> None:
    unknown_specimens = sorted({row["SPECIMEN_ID"].strip() for row in samples.values()} - set(specimens))
    if unknown_specimens:
        raise ValueError(
            "samples.tsv references SPECIMEN_ID values absent from specimens.tsv: " + ", ".join(unknown_specimens)
        )
    library_sample_ids = {row["SAMPLEID"].strip() for row in libraries.values()}
    unknown_library_samples = sorted(library_sample_ids - set(samples))
    if unknown_library_samples:
        raise ValueError(
            "libraries.tsv references SAMPLEID values absent from samples.tsv: " + ", ".join(unknown_library_samples)
        )
    unknown_input_libraries = sorted({row["LIBRARY_ID"].strip() for row in sequencing_inputs.values()} - set(libraries))
    if unknown_input_libraries:
        raise ValueError(
            "sequencing_inputs.tsv references LIBRARY_ID values absent from libraries.tsv: "
            + ", ".join(unknown_input_libraries)
        )
    unknown_unit_samples = sorted({row["SAMPLEID"].strip() for row in analysis_units.values()} - set(samples))
    if unknown_unit_samples:
        raise ValueError(
            "analysis_units.tsv references SAMPLEID values absent from samples.tsv: " + ", ".join(unknown_unit_samples)
        )
    linked_units = {row["ANALYSIS_UNIT_UID"].strip() for row in analysis_unit_inputs.values()}
    linked_inputs = {row["SEQUENCING_INPUT_UID"].strip() for row in analysis_unit_inputs.values()}
    unknown_units = sorted(linked_units - set(analysis_units))
    unknown_inputs = sorted(linked_inputs - set(sequencing_inputs))
    if unknown_units:
        raise ValueError(
            "analysis_unit_inputs.tsv references unknown ANALYSIS_UNIT_UID values: " + ", ".join(unknown_units)
        )
    if unknown_inputs:
        raise ValueError(
            "analysis_unit_inputs.tsv references unknown SEQUENCING_INPUT_UID values: " + ", ".join(unknown_inputs)
        )
    for label, expected, observed in (
        ("library", set(libraries), {row["LIBRARY_ID"] for row in sequencing_inputs.values()}),
        ("sequencing input", set(sequencing_inputs), linked_inputs),
        ("analysis unit", set(analysis_units), linked_units),
    ):
        missing_children = sorted(expected - observed)
        if missing_children:
            raise ValueError(f"{label} key(s) have no required child or link rows: {missing_children}")
    for link in analysis_unit_inputs.values():
        unit_uid = link["ANALYSIS_UNIT_UID"]
        input_uid = link["SEQUENCING_INPUT_UID"]
        sequencing_input = sequencing_inputs[input_uid]
        library = libraries[sequencing_input["LIBRARY_ID"]]
        unit_sample = analysis_units[unit_uid]["SAMPLEID"]
        if library["SAMPLEID"] != unit_sample:
            raise ValueError(
                f"analysis unit {unit_uid!r} selects input {input_uid!r} from sample "
                f"{library['SAMPLEID']!r}, not declared sample {unit_sample!r}"
            )
        if sequencing_input["MODALITY"] != link["ROLE"]:
            raise ValueError(
                f"analysis unit {unit_uid!r} ROLE {link['ROLE']!r} conflicts with "
                f"sequencing input {input_uid!r} MODALITY {sequencing_input['MODALITY']!r}"
            )


def resolve_analysis_units(
    analysis_units: Mapping[str, Mapping[str, str]],
    libraries: Mapping[str, Mapping[str, str]],
    sequencing_inputs: Mapping[str, Mapping[str, str]],
    analysis_unit_inputs: Mapping[str, Mapping[str, str]],
) -> Dict[str, Dict[str, str]]:
    links_by_unit: Dict[str, List[Mapping[str, str]]] = defaultdict(list)
    for link in analysis_unit_inputs.values():
        links_by_unit[link["ANALYSIS_UNIT_UID"]].append(link)
    resolved: Dict[str, Dict[str, str]] = {}
    for unit_uid, unit in analysis_units.items():
        links = links_by_unit[unit_uid]
        input_rows = [sequencing_inputs[link["SEQUENCING_INPUT_UID"]] for link in links]
        library_ids = list(dict.fromkeys(row["LIBRARY_ID"] for row in input_rows))
        library_euids = [libraries[library_id].get("LIBRARY_EUID", "") for library_id in library_ids]
        resolved[unit_uid] = {
            **unit,
            "SELECTED_LIBRARY_IDS": json.dumps(library_ids, separators=(",", ":")),
            "SELECTED_LIBRARY_EUIDS": json.dumps(library_euids, separators=(",", ":")),
            "SELECTED_SEQUENCING_INPUT_UIDS": json.dumps(
                [link["SEQUENCING_INPUT_UID"] for link in links], separators=(",", ":")
            ),
            "SELECTED_INPUT_ROLES": json.dumps([link["ROLE"] for link in links], separators=(",", ":")),
            "SELECTED_INPUT_ORDINALS": json.dumps(
                [int(link["INPUT_ORDINAL"]) for link in links], separators=(",", ":")
            ),
            "SELECTED_INPUT_MODALITIES": json.dumps([row["MODALITY"] for row in input_rows], separators=(",", ":")),
            "SELECTED_INPUT_LAYOUTS": json.dumps([row["LAYOUT"] for row in input_rows], separators=(",", ":")),
        }
    return resolved


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
    analysis_units: Mapping[str, Mapping[str, str]],
    specimens: Mapping[str, Mapping[str, str]],
    samples: Mapping[str, Mapping[str, str]],
    gender_checks: Mapping[str, Mapping[str, str]],
) -> Dict[str, Dict[str, Value]]:
    missing = sorted(set(analysis_units) - set(hybrid_rows))
    unknown = sorted(set(hybrid_rows) - set(analysis_units))
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing analysis units: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown analysis units: {', '.join(unknown)}")
        raise ValueError("Hybrid QC rows must exactly match analysis_units.tsv; " + "; ".join(parts))

    evaluated: Dict[str, Dict[str, Value]] = {}
    for unit_uid, row in hybrid_rows.items():
        sample_id = str(row["sample_id"])
        unit_sample_id = analysis_units[unit_uid]["SAMPLEID"].strip()
        if sample_id != unit_sample_id:
            raise ValueError(
                f"Hybrid QC sample_id '{sample_id}' does not match analysis_units.tsv SAMPLEID "
                f"'{unit_sample_id}' for {unit_uid}"
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
