import json
from pathlib import Path

import pytest

from multiqc import report, reset
from multiqc.base_module import ModuleNoSamplesFound
from multiqc.modules.snakemake_samples.parser import HYBRID_REQUIRED_COLUMNS
from multiqc.modules.snakemake_samples.snakemake_samples import MultiqcModule
from multiqc.types import ModuleId


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
ANALYSIS_UNITS = "ANALYSIS_UNIT_UID\tSAMPLEID\nAU-1\tS1\n"
ANALYSIS_UNIT_INPUTS = (
    "ANALYSIS_UNIT_UID\tSEQUENCING_INPUT_UID\tROLE\tINPUT_ORDINAL\n"
    "AU-1\tINPUT-SR-A\tsr\t1\n"
    "AU-1\tINPUT-SR-B\tsr\t2\n"
    "AU-1\tINPUT-LR\tlr\t3\n"
)
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)

MANIFESTS = {
    "specimens.tsv": SPECIMENS,
    "samples.tsv": SAMPLES,
    "libraries.tsv": LIBRARIES,
    "sequencing_inputs.tsv": SEQUENCING_INPUTS,
    "analysis_units.tsv": ANALYSIS_UNITS,
    "analysis_unit_inputs.tsv": ANALYSIS_UNIT_INPUTS,
}


def hybrid_text() -> str:
    values = {
        "schema_version": "1",
        "analysis_unit_uid": "AU-1",
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
    return (
        "\t".join(HYBRID_REQUIRED_COLUMNS)
        + "\n"
        + "\t".join(values[column] for column in HYBRID_REQUIRED_COLUMNS)
        + "\n"
    )


def search_module(path: Path) -> None:
    reset()
    report.analysis_files = [str(path)]
    report.search_files(["snakemake_samples"])


def write_manifests(path: Path) -> None:
    for name, text in MANIFESTS.items():
        (path / name).write_text(text)


def test_module_renders_exact_six_manifest_model(tmp_path: Path) -> None:
    write_manifests(tmp_path)
    (tmp_path / "reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER)

    search_module(tmp_path)
    module = MultiqcModule()

    assert list(module.specimens_data) == ["SP1"]
    assert list(module.samples_data) == ["S1"]
    assert list(module.libraries_data) == ["LIB-LR", "LIB-SR-A", "LIB-SR-B"]
    assert list(module.sequencing_inputs_data) == [
        "INPUT-LR",
        "INPUT-SR-A",
        "INPUT-SR-B",
    ]
    assert list(module.analysis_units_data) == ["AU-1"]
    assert list(module.analysis_unit_inputs_data) == [
        "AU-1|1|INPUT-SR-A",
        "AU-1|2|INPUT-SR-B",
        "AU-1|3|INPUT-LR",
    ]
    assert json.loads(module.analysis_units_data["AU-1"]["SELECTED_LIBRARY_IDS"]) == [
        "LIB-SR-A",
        "LIB-SR-B",
        "LIB-LR",
    ]
    assert json.loads(module.analysis_units_data["AU-1"]["SELECTED_INPUT_LAYOUTS"]) == [
        "paired_fastq",
        "paired_fastq",
        "single_fastq",
    ]
    for entity, count in (
        ("specimens", 1),
        ("samples", 1),
        ("libraries", 3),
        ("sequencing_inputs", 3),
        ("analysis_units", 1),
        ("analysis_unit_inputs", 3),
    ):
        provenance = module.input_provenance[entity]
        assert provenance["normalized_row_count"] == count
        assert provenance["source_file_count"] == 1
        assert len(provenance["normalized_rows_sha256"]) == 64
    anchors = {section.anchor for section in module.sections}
    assert {
        "snakemake-samples-specimens",
        "snakemake-samples-samples",
        "snakemake-samples-libraries",
        "snakemake-samples-sequencing-inputs",
        "snakemake-samples-analysis-units",
        "snakemake-samples-analysis-unit-inputs",
    } <= anchors


def test_module_renders_analysis_unit_hybrid_qc_and_general_stats(tmp_path: Path) -> None:
    write_manifests(tmp_path)
    (tmp_path / "reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER)
    (tmp_path / "hybrid_seq_batch_qc.tsv").write_text(hybrid_text())

    search_module(tmp_path)
    module = MultiqcModule()

    assert module.hybrid_data["AU-1"]["overall_status"] == "PASS"
    assert "snakemake-samples-hybrid-seq-batch-qc" in {section.anchor for section in module.sections}


def test_hybrid_qc_requires_gender_evidence(tmp_path: Path) -> None:
    write_manifests(tmp_path)
    (tmp_path / "hybrid_seq_batch_qc.tsv").write_text(hybrid_text())

    search_module(tmp_path)
    with pytest.raises(ValueError, match="requires the six manifests"):
        MultiqcModule()


def test_module_reports_no_samples_when_nothing_matches(tmp_path: Path) -> None:
    search_module(tmp_path)
    with pytest.raises(ModuleNoSamplesFound):
        MultiqcModule()


@pytest.mark.parametrize("missing", sorted(MANIFESTS))
def test_module_requires_complete_six_manifest_set(tmp_path: Path, missing: str) -> None:
    write_manifests(tmp_path)
    (tmp_path / missing).unlink()

    search_module(tmp_path)
    with pytest.raises(ValueError, match=missing):
        MultiqcModule()


def test_module_rejects_conflicting_duplicate_manifest_copies(tmp_path: Path) -> None:
    for directory in (tmp_path / "a", tmp_path / "b"):
        directory.mkdir()
        write_manifests(directory)
    (tmp_path / "b/samples.tsv").write_text(SAMPLES.replace("Z-SA-1", "Z-SA-2"))

    search_module(tmp_path)
    with pytest.raises(ValueError, match="Conflicting normalized samples inputs"):
        MultiqcModule()


def test_module_deduplicates_gender_copies_and_rejects_conflicts(tmp_path: Path) -> None:
    write_manifests(tmp_path)
    for directory in (tmp_path / "a", tmp_path / "b"):
        directory.mkdir()
        (directory / "reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER)

    search_module(tmp_path)
    module = MultiqcModule()
    assert list(module.gender_data) == ["S1"]

    (tmp_path / "b/reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER.replace("PASS\ttrue", "FAIL\tfalse"))
    search_module(tmp_path)
    with pytest.raises(ValueError, match="Conflicting normalized gender check inputs"):
        MultiqcModule()


def test_native_patterns_claim_all_six_files_before_custom_content(tmp_path: Path) -> None:
    write_manifests(tmp_path)

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["snakemake_samples", "custom_content"])

    for stem in (
        "specimens",
        "samples",
        "libraries",
        "sequencing_inputs",
        "analysis_units",
        "analysis_unit_inputs",
    ):
        assert len(report.files[ModuleId(f"snakemake_samples/{stem}")]) == 1
    assert not report.files.get(ModuleId("custom_content"))
