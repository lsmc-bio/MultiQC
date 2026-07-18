from pathlib import Path

import pytest

from multiqc import report, reset
from multiqc.types import ModuleId

from multiqc.modules.snakemake_samples.snakemake_samples import MultiqcModule


SPECIMENS = "SPECIMEN_ID\tSPECIMEN_EUID\tBIOLOGICAL_SEX\nSP1\tspec-euid-1\tfemale\n"
SAMPLES = "SAMPLEID\tSAMPLE_EUID\tSPECIMEN_ID\nS1\tsample-euid-1\tSP1\n"
UNIT_UID = "explicit-analysis-unit"
LIBRARIES = f"ANALYSIS_UNIT_UID\tLIBRARY_EUID\tSAMPLEID\n{UNIT_UID}\tlibrary-euid-1\tS1\n"
STAGED_SPECIMENS = (
    "Sample\tinput_origin\tSPECIMEN_ID\tSPECIMEN_EUID\tBIOLOGICAL_SEX\nSP1\tinput_manifest\tSP1\tspec-euid-1\tfemale\n"
)
STAGED_SAMPLES = (
    "Sample\tinput_origin\tSAMPLEID\tSAMPLE_EUID\tSPECIMEN_ID\nS1\tinput_manifest\tS1\tsample-euid-1\tSP1\n"
)
STAGED_LIBRARIES = (
    "Sample\tinput_origin\tANALYSIS_UNIT_UID\tLIBRARY_EUID\tSAMPLEID\n"
    f"{UNIT_UID}\tinput_manifest\t{UNIT_UID}\tlibrary-euid-1\tS1\n"
)
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)


def search_module(path: Path) -> None:
    reset()
    report.analysis_files = [str(path)]
    report.search_files(["snakemake_samples"])


def write_raw_manifests(path: Path) -> None:
    (path / "specimens.tsv").write_text(SPECIMENS)
    (path / "samples.tsv").write_text(SAMPLES)
    (path / "libraries.tsv").write_text(LIBRARIES)


def write_staged_manifests(path: Path) -> None:
    (path / "input_specimens_mqc.tsv").write_text(STAGED_SPECIMENS)
    (path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES)
    (path / "input_libraries_mqc.tsv").write_text(STAGED_LIBRARIES)


def test_module_supports_staged_only_three_manifest_contract(tmp_path: Path) -> None:
    write_staged_manifests(tmp_path)

    search_module(tmp_path)
    module = MultiqcModule()

    assert module.specimens_data == {
        "SP1": {"SPECIMEN_ID": "SP1", "SPECIMEN_EUID": "spec-euid-1", "BIOLOGICAL_SEX": "female"}
    }
    assert module.samples_data == {"S1": {"SAMPLEID": "S1", "SAMPLE_EUID": "sample-euid-1", "SPECIMEN_ID": "SP1"}}
    assert module.libraries_data[UNIT_UID]["SAMPLEID"] == "S1"
    assert module.input_provenance["specimens"]["normalized_row_count"] == 1
    assert module.input_provenance["samples"]["normalized_row_count"] == 1
    assert module.input_provenance["libraries"]["normalized_row_count"] == 1


def test_module_accepts_exact_raw_and_staged_manifest_equivalence(tmp_path: Path) -> None:
    write_raw_manifests(tmp_path)
    write_staged_manifests(tmp_path)

    search_module(tmp_path)
    module = MultiqcModule()

    assert list(module.specimens_data) == ["SP1"]
    assert list(module.samples_data) == ["S1"]
    assert list(module.libraries_data) == [UNIT_UID]
    for entity in ("specimens", "samples", "libraries"):
        provenance = module.input_provenance[entity]
        assert provenance["source_file_count"] == 2
        assert provenance["source_row_counts"] == [1, 1]
        assert len(provenance["normalized_rows_sha256"]) == 64


@pytest.mark.parametrize(
    ("missing", "message"),
    [
        ("specimens.tsv", "specimens.tsv or input_specimens_mqc.tsv"),
        ("samples.tsv", "samples.tsv or input_samples_mqc.tsv"),
        ("libraries.tsv", "libraries.tsv or input_libraries_mqc.tsv"),
    ],
)
def test_module_requires_complete_three_manifest_set(tmp_path: Path, missing: str, message: str) -> None:
    write_raw_manifests(tmp_path)
    (tmp_path / missing).unlink()

    search_module(tmp_path)
    with pytest.raises(ValueError, match=message):
        MultiqcModule()


def test_module_rejects_conflicting_manifests_with_all_paths(tmp_path: Path) -> None:
    write_raw_manifests(tmp_path)
    write_staged_manifests(tmp_path)
    (tmp_path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES.replace("sample-euid-1", "different"))

    search_module(tmp_path)
    with pytest.raises(
        ValueError, match=r"Conflicting normalized samples inputs: .*input_samples_mqc.tsv.*samples.tsv"
    ):
        MultiqcModule()


def test_module_deduplicates_gender_copies_and_rejects_conflicts(tmp_path: Path) -> None:
    write_raw_manifests(tmp_path)
    for directory in (tmp_path / "a", tmp_path / "b"):
        directory.mkdir()
        (directory / "reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER)

    search_module(tmp_path)
    module = MultiqcModule()
    assert list(module.gender_data) == ["S1"]

    (tmp_path / "b" / "reported_vs_inferred_sex_check_mqc.tsv").write_text(GENDER.replace("PASS\ttrue", "FAIL\tfalse"))
    search_module(tmp_path)
    with pytest.raises(ValueError) as exc_info:
        MultiqcModule()
    message = str(exc_info.value)
    assert "Conflicting normalized gender check inputs" in message
    assert "/a/reported_vs_inferred_sex_check_mqc.tsv" in message
    assert "/b/reported_vs_inferred_sex_check_mqc.tsv" in message


def test_native_staged_patterns_precede_custom_content_for_all_three_manifests(tmp_path: Path) -> None:
    write_staged_manifests(tmp_path)

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["snakemake_samples", "custom_content"])

    assert len(report.files[ModuleId("snakemake_samples/specimens")]) == 1
    assert len(report.files[ModuleId("snakemake_samples/samples")]) == 1
    assert len(report.files[ModuleId("snakemake_samples/libraries")]) == 1
    assert not report.files.get(ModuleId("custom_content"))
