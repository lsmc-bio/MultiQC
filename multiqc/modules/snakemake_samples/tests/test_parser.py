import pytest

from multiqc.modules.snakemake_samples.parser import (
    HYBRID_REQUIRED_COLUMNS,
    evaluate_hybrid_qc,
    parse_gender_checks,
    parse_hybrid_qc,
    parse_samples,
    parse_staged_samples,
    parse_staged_units,
    parse_units,
    validate_gender_samples,
    validate_unit_samples,
)


SAMPLES = "SAMPLEID\tBIOLOGICAL_SEX\tSAMPLESOURCE\nS1\tfemale\tblood\n"
UNITS = (
    "RUNID\tSAMPLEID\tEXPERIMENTID\tLANEID\tBARCODEID\tLIBPREP\tSEQ_VENDOR\tSEQ_PLATFORM\n"
    "RUN1\tS1\tEXP1\t1\tBC01\tPCR-FREE\tILMN\tNOVASEQ\n"
)
UNIT_UID = "RUN1-S1-EXP1-1-BC01-PCR-FREE-ILMN-NOVASEQ"
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)
STAGED_SAMPLES = "Sample\tinput_origin\tSAMPLEID\tBIOLOGICAL_SEX\tSAMPLESOURCE\nS1\tinput_manifest\tS1\tfemale\tblood\n"
STAGED_UNITS = (
    "Sample\tinput_origin\tRUNID\tSAMPLEID\tEXPERIMENTID\tLANEID\tBARCODEID\tLIBPREP\t"
    "SEQ_VENDOR\tSEQ_PLATFORM\n"
    f"{UNIT_UID}\tinput_manifest\tRUN1\tS1\tEXP1\t1\tBC01\tPCR-FREE\tILMN\tNOVASEQ\n"
)


def hybrid_text(**overrides: str) -> str:
    values = {
        "schema_version": "1",
        "analysis_unit_uid": UNIT_UID,
        "sample_id": "S1",
        "contamination_estimate_pct": "1.0",
        "contamination_max_pct": "2.0",
        "short_read_coverage_threshold": "30",
        "short_read_bases_above_threshold_pct": "95",
        "short_read_bases_above_threshold_pct_min": "90",
        "long_read_mean_coverage": "15",
        "long_read_mean_coverage_min": "10",
        "long_read_target_10x_pct": "90",
        "long_read_target_10x_pct_min": "80",
        "short_read_target_coverage_threshold": "20",
        "short_read_target_below_threshold_pct": "2",
        "short_read_target_below_threshold_pct_max": "5",
        "hybrid_callable_target_snvs_pct": "99",
        "hybrid_callable_target_snvs_pct_min": "95",
        "coverage_uniformity": "0.9",
        "coverage_uniformity_min": "0.8",
        "coverage_uniformity_max": "1.2",
        "expected_relative_matches": "2",
        "detected_relative_matches": "2",
    }
    values.update(overrides)
    header = "\t".join(HYBRID_REQUIRED_COLUMNS)
    row = "\t".join(values[column] for column in HYBRID_REQUIRED_COLUMNS)
    return f"{header}\n{row}\n"


def parsed_contract():
    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, units = parse_units(UNITS, "units.tsv")
    _, gender = parse_gender_checks(GENDER, "reported_vs_inferred_sex_check_mqc.tsv")
    validate_unit_samples(samples, units)
    validate_gender_samples(samples, gender)
    return samples, units, gender


def test_parses_samples_and_builds_collision_safe_library_key() -> None:
    sample_fields, samples = parse_samples(SAMPLES, "samples.tsv")
    unit_fields, units = parse_units(UNITS, "units.tsv")

    assert sample_fields == ["SAMPLEID", "BIOLOGICAL_SEX", "SAMPLESOURCE"]
    assert samples["S1"]["BIOLOGICAL_SEX"] == "female"
    assert unit_fields[0] == "analysis_unit_uid"
    assert units[UNIT_UID]["SAMPLEID"] == "S1"
    validate_unit_samples(samples, units)


def test_staged_manifests_normalize_exactly_to_raw_manifests() -> None:
    _, raw_samples = parse_samples(SAMPLES, "samples.tsv")
    _, staged_samples = parse_staged_samples(STAGED_SAMPLES, "input_samples_mqc.tsv")
    _, raw_units = parse_units(UNITS, "units.tsv")
    _, staged_units = parse_staged_units(STAGED_UNITS, "input_units_mqc.tsv")

    assert staged_samples == raw_samples
    assert staged_units == raw_units


def test_staged_manifests_require_declared_keys_and_origins() -> None:
    with pytest.raises(ValueError, match="Sample must exactly match SAMPLEID"):
        parse_staged_samples(STAGED_SAMPLES.replace("S1\tinput_manifest", "OTHER\tinput_manifest"), "samples.tsv")
    with pytest.raises(ValueError, match="requires input_origin=input_manifest"):
        parse_staged_samples(STAGED_SAMPLES.replace("input_manifest", "generated_by_snakemake"), "samples.tsv")
    with pytest.raises(ValueError, match="Sample must exactly match analysis_unit_uid"):
        parse_staged_units(STAGED_UNITS.replace(UNIT_UID, "OTHER", 1), "units.tsv")
    with pytest.raises(ValueError, match="input_origin must be one of"):
        parse_staged_units(STAGED_UNITS.replace("input_manifest", "unknown"), "units.tsv")


def test_explicit_analysis_unit_uid_is_authoritative() -> None:
    units_text = "analysis_unit_uid\tSAMPLEID\nexplicit-unit\tS1\n"
    _, units = parse_units(units_text, "units.tsv")
    assert list(units) == ["explicit-unit"]


def test_duplicate_samples_and_unknown_unit_samples_fail_hard() -> None:
    with pytest.raises(ValueError, match="duplicate SAMPLEID 'S1'"):
        parse_samples(SAMPLES + "S1\tfemale\tblood\n", "samples.tsv")

    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, units = parse_units(UNITS.replace("\tS1\t", "\tUNKNOWN\t"), "units.tsv")
    with pytest.raises(ValueError, match="absent from samples.tsv: UNKNOWN"):
        validate_unit_samples(samples, units)


def test_gender_checks_must_match_samples_and_reported_provenance() -> None:
    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    validate_gender_samples(samples, gender)

    _, mismatched = parse_gender_checks(GENDER.replace("S1\tfemale", "S1\tmale"), "gender.tsv")
    with pytest.raises(ValueError, match="does not match samples.tsv"):
        validate_gender_samples(samples, mismatched)


def test_hybrid_qc_all_checks_pass() -> None:
    samples, units, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(), "hybrid_seq_batch_qc.tsv")
    evaluated = evaluate_hybrid_qc(hybrid, units, samples, gender)

    row = evaluated[UNIT_UID]
    assert row["overall_status"] == "PASS"
    assert row["failed_checks"] == 0
    assert row["gender_check"] == "PASS"
    assert row["relative_matches_check"] == "PASS"


@pytest.mark.parametrize(
    ("column", "value", "check"),
    [
        ("contamination_estimate_pct", "2.0", "contamination_check"),
        ("short_read_bases_above_threshold_pct", "90", "short_read_coverage_check"),
        ("long_read_mean_coverage", "10", "long_read_coverage_check"),
        ("long_read_target_10x_pct", "80", "long_read_target_10x_check"),
        ("short_read_target_below_threshold_pct", "5", "short_read_target_low_coverage_check"),
        ("hybrid_callable_target_snvs_pct", "95", "hybrid_callable_snvs_check"),
        ("detected_relative_matches", "1", "relative_matches_check"),
    ],
)
def test_hybrid_strict_boundaries_fail(column: str, value: str, check: str) -> None:
    samples, units, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(**{column: value}), "hybrid_seq_batch_qc.tsv")
    row = evaluate_hybrid_qc(hybrid, units, samples, gender)[UNIT_UID]
    assert row[check] == "FAIL"
    assert row["overall_status"] == "FAIL"


def test_uniformity_bounds_are_inclusive() -> None:
    samples, units, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(coverage_uniformity="0.8"), "hybrid_seq_batch_qc.tsv")
    row = evaluate_hybrid_qc(hybrid, units, samples, gender)[UNIT_UID]
    assert row["uniformity_check"] == "PASS"


def test_hybrid_rows_must_exactly_cover_units() -> None:
    samples, units, gender = parsed_contract()
    with pytest.raises(ValueError, match="missing units"):
        evaluate_hybrid_qc({}, units, samples, gender)


def test_hybrid_rejects_invalid_percent_and_schema() -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        parse_hybrid_qc(hybrid_text(contamination_estimate_pct="101"), "hybrid.tsv")
    with pytest.raises(ValueError, match="requires schema_version 1"):
        parse_hybrid_qc(hybrid_text(schema_version="2"), "hybrid.tsv")
    with pytest.raises(ValueError, match="unexpected column.*extra"):
        text = hybrid_text().replace("\n", "\textra\n", 1).rstrip("\n") + "\tvalue\n"
        parse_hybrid_qc(text, "hybrid.tsv")
    reordered = list(HYBRID_REQUIRED_COLUMNS)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    values = dict(zip(HYBRID_REQUIRED_COLUMNS, hybrid_text().splitlines()[1].split("\t")))
    with pytest.raises(ValueError, match="required schema order"):
        parse_hybrid_qc(
            "\t".join(reordered) + "\n" + "\t".join(values[column] for column in reordered) + "\n", "hybrid.tsv"
        )
