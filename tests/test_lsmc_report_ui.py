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
        "modality": modality,
        "SPECIMEN_ID": "SPECIMEN-TEST-1",
        "SPECIMEN_EUID": "test-specimen-identity-1",
        "SAMPLEID": "SAMPLE-TEST-1",
        "SAMPLE_EUID": "test-sample-identity-1",
        "ANALYSIS_UNIT_UID": "LIBRARY-TEST-1",
        "LIBRARY_EUID": "test-library-identity-1",
        "section": "alignment",
        "grain": "library",
        "pair_endpoint_roles": [],
    }


def write_selector_manifest(path: Path, records: list[dict]) -> Path:
    path.write_text(
        json.dumps({"schema_version": "dayoa-report-selectors-v2", "records": records}),
        encoding="utf-8",
    )
    return path


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
    record["LIBRARY_EUID"] = None
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])

    assert load_dayoa_selector_manifest(str(manifest))["records"] == [record]


def test_selector_manifest_rejects_guessed_blank_euid_placeholders(tmp_path: Path) -> None:
    record = selector_record("record-1")
    record["LIBRARY_EUID"] = ""
    manifest = write_selector_manifest(tmp_path / "selectors.json", [record])

    with pytest.raises(ValueError, match="never a guessed placeholder"):
        load_dayoa_selector_manifest(str(manifest))


def test_lsmc_theme_and_selector_contract_render_in_report(tmp_path: Path) -> None:
    data_file = tmp_path / "data_mqc.txt"
    data_file.write_text("record-1\t100\nrecord-2\t200\n", encoding="utf-8")
    manifest = write_selector_manifest(
        tmp_path / "selectors.json",
        [selector_record("record-1"), selector_record("record-2", "lr")],
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
    assert "test-library-identity-1" in report_html
    assert "Display filters do not alter downloaded data." in report_html


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
