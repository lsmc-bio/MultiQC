import json
from pathlib import Path

import pytest

import multiqc
from multiqc.core.update_config import ClConfig
from multiqc.templates.default import load_dayoa_selector_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


def selector_record(analysis_id: str, modality: str = "sr") -> dict:
    return {
        "MultiQCAnalysisID": analysis_id,
        "display_multiqc_analysis_id": analysis_id,
        "modality": modality,
        "evidence_modality": modality,
        "SPECIMEN_ID": "SPECIMEN-TEST-1",
        "SPECIMEN_EUID": "test-specimen-identity-1",
        "SAMPLEID": "SAMPLE-TEST-1",
        "SAMPLE_EUID": "test-sample-identity-1",
        "ANALYSIS_ID": "ANALYSIS-TEST-1",
        "ANALYSIS_UNIT_UID": "ANALYSIS-UNIT-TEST-1",
        "ANALYSIS_UNIT_EUID": "test-analysis-unit-identity-1",
        "DELIVERY_EUID": "test-delivery-identity-1",
        "LIBRARY_EUID": "test-library-identity-1",
        "LIBRARY_IDS": ["LIBRARY-TEST-1"],
        "LIBRARY_EUIDS": ["test-library-identity-1"],
        "SEQUENCING_INPUT_UIDS": ["INPUT-TEST-1"],
        "INPUT_LIBRARY_IDS": ["LIBRARY-TEST-1"],
        "INPUT_ROLES": ["sr"],
        "INPUT_ORDINALS": [1],
        "INPUT_MODALITIES": ["sr"],
        "INPUT_LAYOUTS": ["paired"],
        "entity_scope": "analysis_unit",
        "selector_eligible": True,
        "general_stats_eligible": True,
        "section": "alignment",
        "grain": "library",
        "pair_endpoint_roles": [],
        "stable_multiqc_record_ids": [analysis_id],
        "original_multiqc_analysis_ids": [analysis_id],
    }


def write_selector_manifest(path: Path, records: list[dict]) -> Path:
    selector_records = [record for record in records if record["selector_eligible"]]
    path.write_text(
        json.dumps(
            {
                "schema_version": "dayoa-report-selectors-v3",
                "records": records,
                "plot_groupings": {},
                "source_staging_manifest": "manifest.tsv",
                "source_row_count": len(records),
                "record_count": len(records),
                "selector_record_count": len(selector_records),
                "selector_records": selector_records,
            }
        ),
        encoding="utf-8",
    )
    return path


def non_selector_record(analysis_id: str) -> dict:
    record = selector_record(analysis_id, "global")
    for field in (
        "SPECIMEN_ID",
        "SPECIMEN_EUID",
        "SAMPLEID",
        "SAMPLE_EUID",
        "ANALYSIS_ID",
        "ANALYSIS_UNIT_UID",
        "ANALYSIS_UNIT_EUID",
        "DELIVERY_EUID",
        "LIBRARY_EUID",
    ):
        record[field] = None
    for field in (
        "LIBRARY_IDS",
        "LIBRARY_EUIDS",
        "SEQUENCING_INPUT_UIDS",
        "INPUT_LIBRARY_IDS",
        "INPUT_ROLES",
        "INPUT_ORDINALS",
        "INPUT_MODALITIES",
        "INPUT_LAYOUTS",
    ):
        record[field] = []
    record["entity_scope"] = "workflow_artifact"
    record["selector_eligible"] = False
    record["general_stats_eligible"] = False
    return record


def test_selector_manifest_rejects_duplicate_analysis_ids(tmp_path: Path) -> None:
    manifest = write_selector_manifest(
        tmp_path / "selectors.json",
        [selector_record("record-1"), selector_record("record-1", "lr")],
    )

    with pytest.raises(ValueError, match="Duplicate MultiQCAnalysisID 'record-1'"):
        load_dayoa_selector_manifest(str(manifest))


def test_selector_manifest_rejects_conflicting_lineage(tmp_path: Path) -> None:
    first = selector_record("record-1")
    second = selector_record("record-2", "lr")
    second["SPECIMEN_EUID"] = "test-specimen-identity-2"
    manifest = write_selector_manifest(tmp_path / "selectors.json", [first, second])

    with pytest.raises(ValueError, match="conflicting specimen identity mapping"):
        load_dayoa_selector_manifest(str(manifest))


def test_selector_manifest_accepts_missing_optional_persisted_euids(tmp_path: Path) -> None:
    record = selector_record("record-1")
    record["SPECIMEN_EUID"] = None
    record["SAMPLE_EUID"] = None
    record["ANALYSIS_UNIT_EUID"] = None
    record["DELIVERY_EUID"] = None
    record["LIBRARY_EUID"] = None
    record["LIBRARY_EUIDS"] = [None]
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])

    assert load_dayoa_selector_manifest(str(manifest))["records"] == [record]


@pytest.mark.parametrize("nullable_record_first", [True, False])
def test_selector_manifest_reconciles_nullable_and_persisted_library_euids(
    tmp_path: Path, nullable_record_first: bool
) -> None:
    nullable_record = selector_record("record-nullable", "sr")
    nullable_record["LIBRARY_EUID"] = None
    nullable_record["LIBRARY_EUIDS"] = [None]
    persisted_record = selector_record("record-persisted", "lr")
    persisted_record["ANALYSIS_UNIT_UID"] = "ANALYSIS-UNIT-TEST-2"
    persisted_record["ANALYSIS_UNIT_EUID"] = "test-analysis-unit-identity-2"
    persisted_record["DELIVERY_EUID"] = "test-delivery-identity-2"
    records = [nullable_record, persisted_record]
    if not nullable_record_first:
        records.reverse()
    manifest = write_selector_manifest(tmp_path / "selectors.json", records)

    assert load_dayoa_selector_manifest(str(manifest))["records"] == records


def test_selector_manifest_accepts_rsr_modality(tmp_path: Path) -> None:
    record = selector_record("record-rsr", "rsr")
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])

    assert load_dayoa_selector_manifest(str(manifest))["records"] == [record]


def test_selector_manifest_rejects_guessed_blank_euid_placeholders(tmp_path: Path) -> None:
    record = selector_record("record-1")
    record["LIBRARY_EUID"] = ""
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])

    with pytest.raises(ValueError, match="never a guessed placeholder"):
        load_dayoa_selector_manifest(str(manifest))


def test_selector_manifest_allows_two_analysis_units_to_share_one_library(tmp_path: Path) -> None:
    first = selector_record("record-1")
    second = selector_record("record-2", "lr")
    second["ANALYSIS_UNIT_UID"] = "ANALYSIS-UNIT-TEST-2"
    second["ANALYSIS_UNIT_EUID"] = "test-analysis-unit-identity-2"
    second["DELIVERY_EUID"] = "test-delivery-identity-2"
    manifest = write_selector_manifest(tmp_path / "selectors.json", [first, second])

    assert load_dayoa_selector_manifest(str(manifest))["records"] == [first, second]


@pytest.mark.parametrize(
    ("library_id", "library_euid"),
    [
        ("LIBRARY-TEST-1", "test-library-identity-2"),
        ("LIBRARY-TEST-2", "test-library-identity-1"),
    ],
)
def test_selector_manifest_rejects_conflicting_physical_library_mapping(
    tmp_path: Path, library_id: str, library_euid: str
) -> None:
    first = selector_record("record-1")
    second = selector_record("record-2", "lr")
    second["ANALYSIS_UNIT_UID"] = "ANALYSIS-UNIT-TEST-2"
    second["ANALYSIS_UNIT_EUID"] = "test-analysis-unit-identity-2"
    second["DELIVERY_EUID"] = "test-delivery-identity-2"
    second["LIBRARY_IDS"] = [library_id]
    second["LIBRARY_EUIDS"] = [library_euid]
    second["LIBRARY_EUID"] = library_euid
    second["INPUT_LIBRARY_IDS"] = [library_id]
    manifest = write_selector_manifest(tmp_path / "selectors.json", [first, second])

    with pytest.raises(ValueError, match="conflicting library identity mapping"):
        load_dayoa_selector_manifest(str(manifest))


def test_selector_manifest_rejects_v2_without_fallback(tmp_path: Path) -> None:
    record = selector_record("record-1")
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["schema_version"] = "dayoa-report-selectors-v2"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="dayoa-report-selectors-v3"):
        load_dayoa_selector_manifest(str(manifest))


def test_selector_manifest_rejects_count_and_subset_mismatch(tmp_path: Path) -> None:
    first = selector_record("record-1")
    second = non_selector_record("workflow-record")
    manifest = write_selector_manifest(tmp_path / "selectors.json", [first, second])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["record_count"] = 1
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="record_count must equal 2"):
        load_dayoa_selector_manifest(str(manifest))

    payload["record_count"] = 2
    payload["selector_records"] = [second]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="selector_records must exactly equal"):
        load_dayoa_selector_manifest(str(manifest))


def test_non_sample_records_are_not_selector_records(tmp_path: Path) -> None:
    selector = selector_record("record-1")
    workflow = non_selector_record("workflow-record")
    manifest = write_selector_manifest(tmp_path / "selectors.json", [selector, workflow])

    loaded = load_dayoa_selector_manifest(str(manifest))

    assert loaded["records"] == [selector, workflow]
    assert loaded["selector_records"] == [selector]


def test_lsmc_theme_and_selector_contract_render_in_report(tmp_path: Path) -> None:
    data_file = tmp_path / "data_mqc.txt"
    data_file.write_text("record-1\t100\nrecord-2\t200\n", encoding="utf-8")
    manifest = write_selector_manifest(
        tmp_path / "selectors.json",
        [
            selector_record("record-1"),
            selector_record("record-rsr", "rsr"),
            selector_record("record-2", "lr"),
        ],
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f'dayoa_report_selectors: "{manifest}"\nlsmc_default_theme: "lsmc"\n',
        encoding="utf-8",
    )

    multiqc.run(
        data_file,
        cfg=ClConfig(force=True, output_dir=str(tmp_path), config_files=[config_file]),
    )

    report_html = (tmp_path / "multiqc_report.html").read_text(encoding="utf-8")
    assert 'data-theme="lsmc"' in report_html
    assert 'id="dayoa_report_selectors"' in report_html
    assert 'id="dayoa-selector-panel"' in report_html
    assert 'data-theme-value="original"' in report_html
    assert 'data-theme-value="nosee"' in report_html
    assert 'data-theme-value="tacky"' not in report_html
    assert "Nunito Sans" in report_html
    assert "Source Serif 4" in report_html
    assert "test-analysis-unit-identity-1" in report_html
    assert "Analysis units" in report_html
    assert "Display filters do not alter downloaded data." in report_html
    expected_buttons = (
        ("all", "All analysis outputs", "All"),
        ("sr", "Short Read", "SR only"),
        ("rsr", "Realigned Short Read", "RSR only"),
        ("lr", "Long Read", "LR only"),
        ("hybrid", "Hybrid Short Read + Long Read", "Hybrid only"),
    )
    prior_index = -1
    for modality, accessible_label, visible_label in expected_buttons:
        fragment = (
            f'data-modality="{modality}"'
            f' aria-pressed="{"true" if modality == "all" else "false"}"'
            f' aria-label="{accessible_label}" title="{accessible_label}"'
            f'>{visible_label}</button>'
        )
        assert fragment in report_html
        index = report_html.index(fragment)
        assert index > prior_index
        prior_index = index


def test_unconfigured_report_has_no_dayoa_selector_controls(tmp_path: Path) -> None:
    data_file = tmp_path / "data_mqc.txt"
    data_file.write_text("record-1\t100\n", encoding="utf-8")

    multiqc.run(data_file, cfg=ClConfig(force=True, output_dir=str(tmp_path)))

    report_html = (tmp_path / "multiqc_report.html").read_text(encoding="utf-8")
    assert 'id="dayoa_report_selectors"' not in report_html
    assert 'id="dayoa-selector-panel"' not in report_html


def test_lsmc_compact_logo_is_upper_right_and_print_safe() -> None:
    header = (REPO_ROOT / "multiqc/templates/default/header.html").read_text(encoding="utf-8")
    styles = (REPO_ROOT / "multiqc/templates/default/src/scss/_lsmc.scss").read_text(encoding="utf-8")

    brand_start = header.index('<div class="lsmc-native-brand"')
    brand_end = header.index("</div>", brand_start)
    brand = header[brand_start:brand_end]
    assert brand.index("lsmc-report-kicker") < brand.index("lsmc-compact-black-transparent.png")
    assert "justify-content: flex-end;" in styles
    assert 'html[data-theme="lsmc"]:not([data-theme="original"]) .lsmc-native-logo-on-dark' in styles
    assert 'html[data-theme]:not([data-theme="original"]) .lsmc-native-logo-on-light' in styles
    assert "display: block !important;" in styles
    assert 'html[data-theme]:not([data-theme="original"]) .lsmc-native-logo-on-dark' in styles
    assert "display: none !important;" in styles


def test_selector_typography_is_reduced_by_exactly_one_point_locally() -> None:
    styles = (REPO_ROOT / "multiqc/templates/default/src/scss/_lsmc.scss").read_text(encoding="utf-8")

    assert "font-size: calc(0.85rem - 1pt);" in styles
    assert "font-size: calc(1.125rem - 1pt);" in styles
    assert "font-size: calc(0.7rem - 1pt);" in styles
    assert "font-size: calc(0.74375rem - 1pt);" in styles
    assert "font-size: calc(0.75rem - 1pt);" in styles
    assert "font: 650 calc(0.72rem - 1pt) / 1.2" in styles
    assert "body {\n  font-size: calc" not in styles
