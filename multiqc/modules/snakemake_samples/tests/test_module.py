from pathlib import Path

import pytest

from multiqc import report, reset
from multiqc.types import ModuleId

from multiqc.modules.snakemake_samples.snakemake_samples import MultiqcModule


SAMPLES = "SAMPLEID\tBIOLOGICAL_SEX\nS1\tfemale\n"
STAGED_SAMPLES = "Sample\tinput_origin\tSAMPLEID\tBIOLOGICAL_SEX\nS1\tinput_manifest\tS1\tfemale\n"
UNIT_UID = "RUN1-S1-EXP1-1-BC01-PCR-FREE-ILMN-NOVASEQ"
UNITS = (
    "RUNID\tSAMPLEID\tEXPERIMENTID\tLANEID\tBARCODEID\tLIBPREP\tSEQ_VENDOR\tSEQ_PLATFORM\n"
    "RUN1\tS1\tEXP1\t1\tBC01\tPCR-FREE\tILMN\tNOVASEQ\n"
)
STAGED_UNITS = (
    "Sample\tinput_origin\tRUNID\tSAMPLEID\tEXPERIMENTID\tLANEID\tBARCODEID\tLIBPREP\t"
    "SEQ_VENDOR\tSEQ_PLATFORM\n"
    f"{UNIT_UID}\tinput_manifest\tRUN1\tS1\tEXP1\t1\tBC01\tPCR-FREE\tILMN\tNOVASEQ\n"
)
GENDER = (
    "Sample\treported_sex_raw\tinferred_sex_chromosome_complement\tcomparison_status\tcomparison_pass\n"
    "S1\tfemale\tXX\tPASS\ttrue\n"
)


def search_module(path: Path) -> None:
    reset()
    report.analysis_files = [str(path)]
    report.search_files(["snakemake_samples"])


def test_module_supports_staged_only_manifests(tmp_path: Path) -> None:
    (tmp_path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES)
    (tmp_path / "input_units_mqc.tsv").write_text(STAGED_UNITS)

    search_module(tmp_path)
    module = MultiqcModule()

    assert module.samples_data == {"S1": {"SAMPLEID": "S1", "BIOLOGICAL_SEX": "female"}}
    assert module.units_data[UNIT_UID]["SAMPLEID"] == "S1"


def test_module_accepts_exact_raw_and_staged_manifest_equivalence(tmp_path: Path) -> None:
    (tmp_path / "samples.tsv").write_text(SAMPLES)
    (tmp_path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES)
    (tmp_path / "units.tsv").write_text(UNITS)
    (tmp_path / "input_units_mqc.tsv").write_text(STAGED_UNITS)

    search_module(tmp_path)
    module = MultiqcModule()

    assert list(module.samples_data) == ["S1"]
    assert list(module.units_data) == [UNIT_UID]


def test_module_rejects_conflicting_manifests_with_all_paths(tmp_path: Path) -> None:
    (tmp_path / "samples.tsv").write_text(SAMPLES)
    (tmp_path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES.replace("female", "male"))

    search_module(tmp_path)
    with pytest.raises(
        ValueError, match=r"Conflicting normalized samples inputs: .*input_samples_mqc.tsv.*samples.tsv"
    ):
        MultiqcModule()


def test_module_deduplicates_gender_copies_and_rejects_conflicts(tmp_path: Path) -> None:
    (tmp_path / "samples.tsv").write_text(SAMPLES)
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


def test_native_staged_patterns_precede_custom_content(tmp_path: Path) -> None:
    (tmp_path / "input_samples_mqc.tsv").write_text(STAGED_SAMPLES)

    reset()
    report.analysis_files = [str(tmp_path)]
    report.search_files(["snakemake_samples", "custom_content"])

    assert len(report.files[ModuleId("snakemake_samples/samples")]) == 1
    assert not report.files.get(ModuleId("custom_content"))
