import json

import pytest

from multiqc.modules.snakemake_samples.parser import (
    HYBRID_REQUIRED_COLUMNS,
    evaluate_hybrid_qc,
    parse_analysis_unit_inputs,
    parse_analysis_units,
    parse_gender_checks,
    parse_hybrid_qc,
    parse_libraries,
    parse_samples,
    parse_sequencing_inputs,
    parse_specimens,
    parse_tsv,
    resolve_analysis_units,
    validate_gender_samples,
    validate_manifest_lineage,
)


SPECIMENS = "SPECIMEN_ID\tSPECIMEN_EUID\tBIOLOGICAL_SEX\nSP1\tZ-SP-1\tfemale\n"
SAMPLES = "SAMPLEID\tSAMPLE_EUID\tSPECIMEN_ID\nS1\tZ-SA-1\tSP1\n"
LIBRARIES = (
    "LIBRARY_ID\tLIBRARY_EUID\tSAMPLEID\nLIB-LR\tZ-LIB-LR\tS1\nLIB-SR-A\tZ-LIB-SR-A\tS1\nLIB-SR-B\tZ-LIB-SR-B\tS1\n"
)
SEQUENCING_INPUTS = (
    "SEQUENCING_INPUT_UID\tLIBRARY_ID\tMODALITY\tLAYOUT\n"
    "INPUT-LR\tLIB-LR\tlr\tsingle_fastq\n"
    "INPUT-SR-A\tLIB-SR-A\tsr\tpaired_fastq\n"
    "INPUT-SR-B\tLIB-SR-B\tsr\tpaired_fastq\n"
)
UNIT_UID = "AU-1"
ANALYSIS_UNITS = f"ANALYSIS_UNIT_UID\tANALYSIS_UNIT_EUID\tSAMPLEID\n{UNIT_UID}\tZ-AU-1\tS1\n"
ANALYSIS_UNIT_INPUTS = (
    "ANALYSIS_UNIT_UID\tSEQUENCING_INPUT_UID\tROLE\tINPUT_ORDINAL\n"
    f"{UNIT_UID}\tINPUT-SR-A\tsr\t1\n"
    f"{UNIT_UID}\tINPUT-SR-B\tsr\t2\n"
    f"{UNIT_UID}\tINPUT-LR\tlr\t3\n"
)
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)


def parsed_contract():
    _, specimens = parse_specimens(SPECIMENS, "specimens.tsv")
    _, samples = parse_samples(SAMPLES, "samples.tsv")
    _, libraries = parse_libraries(LIBRARIES, "libraries.tsv")
    _, sequencing_inputs = parse_sequencing_inputs(SEQUENCING_INPUTS, "sequencing_inputs.tsv")
    _, analysis_units = parse_analysis_units(ANALYSIS_UNITS, "analysis_units.tsv")
    _, links = parse_analysis_unit_inputs(ANALYSIS_UNIT_INPUTS, "analysis_unit_inputs.tsv")
    validate_manifest_lineage(specimens, samples, libraries, sequencing_inputs, analysis_units, links)
    return specimens, samples, libraries, sequencing_inputs, analysis_units, links


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
    return (
        "\t".join(HYBRID_REQUIRED_COLUMNS)
        + "\n"
        + "\t".join(values[column] for column in HYBRID_REQUIRED_COLUMNS)
        + "\n"
    )


def test_parses_exact_six_manifest_grains_and_resolves_ordered_inputs() -> None:
    specimens, samples, libraries, sequencing_inputs, analysis_units, links = parsed_contract()
    assert list(specimens) == ["SP1"]
    assert list(samples) == ["S1"]
    assert list(libraries) == ["LIB-LR", "LIB-SR-A", "LIB-SR-B"]
    assert list(sequencing_inputs) == ["INPUT-LR", "INPUT-SR-A", "INPUT-SR-B"]
    assert list(analysis_units) == [UNIT_UID]
    assert list(links) == [
        f"{UNIT_UID}|1|INPUT-SR-A",
        f"{UNIT_UID}|2|INPUT-SR-B",
        f"{UNIT_UID}|3|INPUT-LR",
    ]

    row = resolve_analysis_units(analysis_units, libraries, sequencing_inputs, links)[UNIT_UID]
    assert json.loads(row["SELECTED_LIBRARY_IDS"]) == [
        "LIB-SR-A",
        "LIB-SR-B",
        "LIB-LR",
    ]
    assert json.loads(row["SELECTED_SEQUENCING_INPUT_UIDS"]) == [
        "INPUT-SR-A",
        "INPUT-SR-B",
        "INPUT-LR",
    ]
    assert json.loads(row["SELECTED_INPUT_ROLES"]) == ["sr", "sr", "lr"]
    assert json.loads(row["SELECTED_INPUT_ORDINALS"]) == [1, 2, 3]
    assert json.loads(row["SELECTED_INPUT_MODALITIES"]) == ["sr", "sr", "lr"]
    assert json.loads(row["SELECTED_INPUT_LAYOUTS"]) == [
        "paired_fastq",
        "paired_fastq",
        "single_fastq",
    ]


def test_old_library_as_analysis_unit_shape_is_rejected() -> None:
    old = "ANALYSIS_UNIT_UID\tSAMPLEID\nAU-1\tS1\n"
    with pytest.raises(ValueError, match="missing required column.*LIBRARY_ID"):
        parse_libraries(old, "libraries.tsv")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (None, "Could not read"),
        ("", "no header"),
        ("A\tA\n1\t2\n", "duplicate column"),
        ("A\n1\textra\n", "more fields"),
        ("A\tB\n1\n", "fewer fields"),
        ("A\tB\n", "no data rows"),
    ],
)
def test_parse_tsv_rejects_malformed_inputs(text, message) -> None:
    with pytest.raises(ValueError, match=message):
        parse_tsv(text, "bad.tsv", "test")


@pytest.mark.parametrize(
    ("text", "parser", "filename", "message"),
    [
        (SPECIMENS + "SP1\tZ-OTHER\tmale\n", parse_specimens, "specimens.tsv", "duplicate SPECIMEN_ID"),
        (SAMPLES + "S1\tZ-OTHER\tSP1\n", parse_samples, "samples.tsv", "duplicate SAMPLEID"),
        (LIBRARIES + "LIB-LR\tZ-OTHER\tS1\n", parse_libraries, "libraries.tsv", "duplicate LIBRARY_ID"),
        (
            SEQUENCING_INPUTS + "INPUT-LR\tLIB-LR\tlr\tsingle_fastq\n",
            parse_sequencing_inputs,
            "sequencing_inputs.tsv",
            "duplicate SEQUENCING_INPUT_UID",
        ),
        (
            ANALYSIS_UNITS + f"{UNIT_UID}\tZ-OTHER\tS1\n",
            parse_analysis_units,
            "analysis_units.tsv",
            "duplicate ANALYSIS_UNIT_UID",
        ),
    ],
)
def test_duplicate_entity_keys_fail(text, parser, filename, message) -> None:
    with pytest.raises(ValueError, match=message):
        parser(text, filename)


def test_join_requires_exact_contiguous_order_and_unique_input_selection() -> None:
    with pytest.raises(ValueError, match="exact contiguous order"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("\tsr\t2\n", "\tsr\t3\n", 1),
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="more than once"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("INPUT-SR-B", "INPUT-SR-A"),
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="missing required column"):
        parse_analysis_unit_inputs(
            "ANALYSIS_UNIT_UID\tSEQUENCING_INPUT_UID\tROLE\nAU-1\tI-1\tsr\n",
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="blank required column"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("\tsr\t1", "\t\t1", 1),
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="ROLE must be one of"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("\tsr\t1", "\tother\t1", 1),
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="positive integer"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("\tsr\t1", "\tsr\tbad", 1),
            "analysis_unit_inputs.tsv",
        )
    with pytest.raises(ValueError, match="canonical positive integer"):
        parse_analysis_unit_inputs(
            ANALYSIS_UNIT_INPUTS.replace("\tsr\t1", "\tsr\t01", 1),
            "analysis_unit_inputs.tsv",
        )


@pytest.mark.parametrize(
    ("column", "bad_value"),
    [("MODALITY", "hybrid"), ("LAYOUT", "paired")],
)
def test_sequencing_input_literals_are_exact(column: str, bad_value: str) -> None:
    fieldnames, first_row = SEQUENCING_INPUTS.splitlines()[:2]
    columns = fieldnames.split("\t")
    values = first_row.split("\t")
    values[columns.index(column)] = bad_value
    invalid = fieldnames + "\n" + "\t".join(values) + "\n"
    with pytest.raises(ValueError, match=rf"{column} must be one of"):
        parse_sequencing_inputs(invalid, "sequencing_inputs.tsv")


def test_lineage_rejects_role_modality_and_cross_sample_conflicts() -> None:
    specimens, samples, libraries, sequencing_inputs, analysis_units, links = parsed_contract()
    mismatched_inputs = {
        key: ({**row, "MODALITY": "lr"} if key == "INPUT-SR-A" else row) for key, row in sequencing_inputs.items()
    }
    with pytest.raises(ValueError, match="ROLE 'sr'.*MODALITY 'lr'"):
        validate_manifest_lineage(
            specimens,
            samples,
            libraries,
            mismatched_inputs,
            analysis_units,
            links,
        )

    other_samples = {**samples, "S2": {**samples["S1"], "SAMPLEID": "S2"}}
    other_libraries = {key: ({**row, "SAMPLEID": "S2"} if key == "LIB-SR-A" else row) for key, row in libraries.items()}
    with pytest.raises(ValueError, match="not declared sample"):
        validate_manifest_lineage(
            specimens,
            other_samples,
            other_libraries,
            sequencing_inputs,
            analysis_units,
            links,
        )


def test_lineage_rejects_orphans_and_unselected_entities() -> None:
    specimens, samples, libraries, sequencing_inputs, analysis_units, links = parsed_contract()
    with pytest.raises(ValueError, match="absent from specimens.tsv"):
        validate_manifest_lineage({}, samples, libraries, sequencing_inputs, analysis_units, links)
    with pytest.raises(ValueError, match="absent from libraries.tsv"):
        validate_manifest_lineage(
            specimens,
            samples,
            libraries,
            {**sequencing_inputs, "ORPHAN": {**sequencing_inputs["INPUT-LR"], "LIBRARY_ID": "UNKNOWN"}},
            analysis_units,
            links,
        )
    with pytest.raises(ValueError, match="unknown ANALYSIS_UNIT_UID"):
        validate_manifest_lineage(
            specimens,
            samples,
            libraries,
            sequencing_inputs,
            analysis_units,
            {**links, "orphan": {**next(iter(links.values())), "ANALYSIS_UNIT_UID": "UNKNOWN"}},
        )
    with pytest.raises(ValueError, match="sequencing input key.*no required child"):
        validate_manifest_lineage(
            specimens,
            samples,
            libraries,
            {**sequencing_inputs, "UNUSED": {**sequencing_inputs["INPUT-LR"], "SEQUENCING_INPUT_UID": "UNUSED"}},
            analysis_units,
            links,
        )


def test_gender_and_hybrid_qc_are_analysis_unit_scoped() -> None:
    specimens, samples, _libraries, _inputs, analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    validate_gender_samples(specimens, samples, gender)
    _, hybrid = parse_hybrid_qc(hybrid_text(), "hybrid.tsv")
    row = evaluate_hybrid_qc(hybrid, analysis_units, specimens, samples, gender)[UNIT_UID]
    assert row["overall_status"] == "PASS"
    assert row["failed_checks"] == 0


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
    specimens, samples, _libraries, _inputs, analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    _, hybrid = parse_hybrid_qc(hybrid_text(**{column: value}), "hybrid.tsv")
    row = evaluate_hybrid_qc(hybrid, analysis_units, specimens, samples, gender)[UNIT_UID]
    assert row[check] == "FAIL"
    assert row["overall_status"] == "FAIL"


def test_hybrid_rows_must_exactly_cover_analysis_units() -> None:
    specimens, samples, _libraries, _inputs, analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    with pytest.raises(ValueError, match="missing analysis units"):
        evaluate_hybrid_qc({}, analysis_units, specimens, samples, gender)


def test_gender_checks_match_samples_and_specimen_provenance() -> None:
    specimens, samples, _libraries, _inputs, _analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    validate_gender_samples(specimens, samples, gender)

    _, mismatched = parse_gender_checks(GENDER.replace("S1\tfemale", "S1\tmale"), "gender.tsv")
    with pytest.raises(ValueError, match="does not match specimens.tsv"):
        validate_gender_samples(specimens, samples, mismatched)
    with pytest.raises(ValueError, match="must contain BIOLOGICAL_SEX"):
        validate_gender_samples({"SP1": {"SPECIMEN_ID": "SP1"}}, samples, gender)
    with pytest.raises(ValueError, match="missing check rows"):
        validate_gender_samples(specimens, samples, {})
    with pytest.raises(ValueError, match="invalid comparison_pass"):
        parse_gender_checks(GENDER.replace("PASS\ttrue", "PASS\tmaybe"), "gender.tsv")
    with pytest.raises(ValueError, match="PASS row must set"):
        parse_gender_checks(GENDER.replace("PASS\ttrue", "PASS\tfalse"), "gender.tsv")


def test_uniformity_bounds_are_inclusive() -> None:
    specimens, samples, _libraries, _inputs, analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    _, hybrid = parse_hybrid_qc(hybrid_text(coverage_uniformity="0.8"), "hybrid.tsv")
    row = evaluate_hybrid_qc(hybrid, analysis_units, specimens, samples, gender)[UNIT_UID]
    assert row["uniformity_check"] == "PASS"


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
            "\t".join(reordered) + "\n" + "\t".join(values[column] for column in reordered) + "\n",
            "hybrid.tsv",
        )
    with pytest.raises(ValueError, match="must be numeric"):
        parse_hybrid_qc(hybrid_text(contamination_estimate_pct="not-a-number"), "hybrid.tsv")
    with pytest.raises(ValueError, match="must be finite"):
        parse_hybrid_qc(hybrid_text(contamination_estimate_pct="nan"), "hybrid.tsv")
    with pytest.raises(ValueError, match="must be nonnegative"):
        parse_hybrid_qc(hybrid_text(long_read_mean_coverage="-1"), "hybrid.tsv")
    with pytest.raises(ValueError, match="uniformity minimum exceeds maximum"):
        parse_hybrid_qc(hybrid_text(coverage_uniformity_min="2"), "hybrid.tsv")


def test_hybrid_rejects_wrong_sample_and_unknown_units() -> None:
    specimens, samples, _libraries, _inputs, analysis_units, _links = parsed_contract()
    _, gender = parse_gender_checks(GENDER, "gender.tsv")
    _, wrong_sample = parse_hybrid_qc(hybrid_text(sample_id="OTHER"), "hybrid.tsv")
    with pytest.raises(ValueError, match="does not match analysis_units.tsv"):
        evaluate_hybrid_qc(wrong_sample, analysis_units, specimens, samples, gender)
    _, unknown = parse_hybrid_qc(hybrid_text(analysis_unit_uid="AU-OTHER"), "hybrid.tsv")
    with pytest.raises(ValueError, match="unknown analysis units"):
        evaluate_hybrid_qc(unknown, analysis_units, specimens, samples, gender)
