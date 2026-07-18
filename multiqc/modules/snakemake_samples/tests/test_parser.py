import pytest

from multiqc.modules.snakemake_samples.parser import (
    HYBRID_REQUIRED_COLUMNS,
    evaluate_hybrid_qc,
    parse_gender_checks,
    parse_hybrid_qc,
    parse_libraries,
    parse_samples,
    parse_specimens,
    parse_staged_libraries,
    parse_staged_samples,
    parse_staged_specimens,
    validate_gender_samples,
    validate_manifest_lineage,
)


SPECIMENS = "SPECIMEN_ID\tSPECIMEN_EUID\tBIOLOGICAL_SEX\tSAMPLESOURCE\nSP1\tspec-euid-1\tfemale\tblood\n"
SAMPLES = "SAMPLEID\tSAMPLE_EUID\tSPECIMEN_ID\nS1\tsample-euid-1\tSP1\n"
UNIT_UID = "explicit-analysis-unit"
LIBRARIES = (
    "ANALYSIS_UNIT_UID\tLIBRARY_EUID\tSAMPLEID\tRUNID\tSEQ_VENDOR\tSEQ_PLATFORM\n"
    f"{UNIT_UID}\tlibrary-euid-1\tS1\tRUN1\tILMN\tNOVASEQ\n"
)
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)
STAGED_SPECIMENS = (
    "Sample\tinput_origin\tSPECIMEN_ID\tSPECIMEN_EUID\tBIOLOGICAL_SEX\tSAMPLESOURCE\n"
    "SP1\tinput_manifest\tSP1\tspec-euid-1\tfemale\tblood\n"
)
STAGED_SAMPLES = (
    "Sample\tinput_origin\tSAMPLEID\tSAMPLE_EUID\tSPECIMEN_ID\nS1\tinput_manifest\tS1\tsample-euid-1\tSP1\n"
)
STAGED_LIBRARIES = (
    "Sample\tinput_origin\tANALYSIS_UNIT_UID\tLIBRARY_EUID\tSAMPLEID\tRUNID\tSEQ_VENDOR\tSEQ_PLATFORM\n"
    f"{UNIT_UID}\tinput_manifest\t{UNIT_UID}\tlibrary-euid-1\tS1\tRUN1\tILMN\tNOVASEQ\n"
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
    _, specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, libraries = parse_libraries(LIBRARIES, "libraries.tsv")
    _, gender = parse_gender_checks(GENDER, "reported_vs_inferred_sex_check_mqc.tsv")
    validate_manifest_lineage(specimens, samples, libraries)
    validate_gender_samples(specimens, samples, gender)
    return specimens, samples, libraries, gender


def test_parses_three_distinct_manifest_grains_and_exact_keys() -> None:
    specimen_fields, specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    sample_fields, samples = parse_samples(SAMPLES, "samples.tsv")
    library_fields, libraries = parse_libraries(LIBRARIES, "libraries.tsv")

    assert specimen_fields == ["SPECIMEN_ID", "SPECIMEN_EUID", "BIOLOGICAL_SEX", "SAMPLESOURCE"]
    assert sample_fields == ["SAMPLEID", "SAMPLE_EUID", "SPECIMEN_ID"]
    assert library_fields[0] == "ANALYSIS_UNIT_UID"
    assert list(specimens) == ["SP1"]
    assert list(samples) == ["S1"]
    assert list(libraries) == [UNIT_UID]
    validate_manifest_lineage(specimens, samples, libraries)


def test_staged_manifests_reconcile_exactly_to_raw_manifests() -> None:
    _, raw_specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    _, staged_specimens = parse_staged_specimens(STAGED_SPECIMENS, "input_specimens_mqc.tsv")
    _, raw_samples = parse_samples(SAMPLES, "samples.tsv")
    _, staged_samples = parse_staged_samples(STAGED_SAMPLES, "input_samples_mqc.tsv")
    _, raw_libraries = parse_libraries(LIBRARIES, "libraries.tsv")
    _, staged_libraries = parse_staged_libraries(STAGED_LIBRARIES, "input_libraries_mqc.tsv")

    assert staged_specimens == raw_specimens
    assert staged_samples == raw_samples
    assert staged_libraries == raw_libraries


def test_staged_manifests_require_exact_declared_keys_and_origins() -> None:
    with pytest.raises(ValueError, match="Sample must exactly match SPECIMEN_ID"):
        parse_staged_specimens(
            STAGED_SPECIMENS.replace("SP1\tinput_manifest", "OTHER\tinput_manifest"), "specimens.tsv"
        )
    with pytest.raises(ValueError, match="Sample must exactly match SAMPLEID"):
        parse_staged_samples(STAGED_SAMPLES.replace("S1\tinput_manifest", "OTHER\tinput_manifest"), "samples.tsv")
    with pytest.raises(ValueError, match="Sample must exactly match ANALYSIS_UNIT_UID"):
        parse_staged_libraries(STAGED_LIBRARIES.replace(UNIT_UID, "OTHER", 1), "libraries.tsv")
    with pytest.raises(ValueError, match="input_origin must be one of"):
        parse_staged_libraries(STAGED_LIBRARIES.replace("input_manifest", "unknown"), "libraries.tsv")


def test_analysis_unit_uid_is_required_and_authoritative() -> None:
    _, libraries = parse_libraries("ANALYSIS_UNIT_UID\tSAMPLEID\nexplicit-unit\tS1\n", "libraries.tsv")
    assert list(libraries) == ["explicit-unit"]
    with pytest.raises(ValueError, match="missing required column.*ANALYSIS_UNIT_UID"):
        parse_libraries("SAMPLEID\nS1\n", "libraries.tsv")
    with pytest.raises(ValueError, match="blank ANALYSIS_UNIT_UID"):
        parse_libraries("ANALYSIS_UNIT_UID\tSAMPLEID\n\tS1\n", "libraries.tsv")


def test_duplicates_and_orphan_lineage_fail_hard() -> None:
    with pytest.raises(ValueError, match="duplicate SPECIMEN_ID 'SP1'"):
        parse_specimens(SPECIMENS + "SP1\tother\tmale\tsaliva\n", "specimens.tsv")
    with pytest.raises(ValueError, match="duplicate SAMPLEID 'S1'"):
        parse_samples(SAMPLES + "S1\tother\tSP1\n", "samples.tsv")
    with pytest.raises(ValueError, match=f"duplicate ANALYSIS_UNIT_UID '{UNIT_UID}'"):
        parse_libraries(LIBRARIES + LIBRARIES.splitlines()[1] + "\n", "libraries.tsv")

    _, specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    _, samples = parse_samples(SAMPLES.replace("\tSP1\n", "\tUNKNOWN\n"), "samples.tsv")
    _, libraries = parse_libraries(LIBRARIES, "libraries.tsv")
    with pytest.raises(ValueError, match="absent from specimens.tsv: UNKNOWN"):
        validate_manifest_lineage(specimens, samples, libraries)

    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, libraries = parse_libraries(LIBRARIES.replace("\tS1\t", "\tUNKNOWN\t"), "libraries.tsv")
    with pytest.raises(ValueError, match="absent from samples.tsv: UNKNOWN"):
        validate_manifest_lineage(specimens, samples, libraries)


def test_gender_checks_match_samples_and_specimen_provenance() -> None:
    _, specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    validate_gender_samples(specimens, samples, gender)

    _, mismatched = parse_gender_checks(GENDER.replace("S1\tfemale", "S1\tmale"), "gender.tsv")
    with pytest.raises(ValueError, match="does not match specimens.tsv"):
        validate_gender_samples(specimens, samples, mismatched)


def test_hybrid_qc_all_checks_pass() -> None:
    specimens, samples, libraries, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(), "hybrid_seq_batch_qc.tsv")
    evaluated = evaluate_hybrid_qc(hybrid, libraries, specimens, samples, gender)

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
    specimens, samples, libraries, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(**{column: value}), "hybrid_seq_batch_qc.tsv")
    row = evaluate_hybrid_qc(hybrid, libraries, specimens, samples, gender)[UNIT_UID]
    assert row[check] == "FAIL"
    assert row["overall_status"] == "FAIL"


def test_uniformity_bounds_are_inclusive() -> None:
    specimens, samples, libraries, gender = parsed_contract()
    _, hybrid = parse_hybrid_qc(hybrid_text(coverage_uniformity="0.8"), "hybrid_seq_batch_qc.tsv")
    row = evaluate_hybrid_qc(hybrid, libraries, specimens, samples, gender)[UNIT_UID]
    assert row["uniformity_check"] == "PASS"


def test_hybrid_rows_must_exactly_cover_libraries() -> None:
    specimens, samples, libraries, gender = parsed_contract()
    with pytest.raises(ValueError, match="missing libraries"):
        evaluate_hybrid_qc({}, libraries, specimens, samples, gender)


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
