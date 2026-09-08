import base64
import gzip
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner

import multiqc
from multiqc import config
from multiqc.core.paginated import extract_tables, group_pages
from multiqc.core.presentation import ASSETS, load_presentation, main, safe_url
from multiqc.core.update_config import ClConfig


@pytest.mark.parametrize("theme", ["original", "lsmc", "light", "nosee", "tacky"])
def test_only_current_lsmc_logo_is_shipped_and_used(theme, monkeypatch):
    config.reset()
    monkeypatch.setenv("MULTIQC_REPORT_STYLE", json.dumps({"default_theme": theme, "allow_tacky": True}))
    logo = (ASSETS / "assets/img/lsmc-compact-black-transparent.png").read_bytes()
    expected = "data:image/png;base64," + base64.b64encode(logo).decode("ascii")
    dark = "data:image/png;base64," + base64.b64encode(
        (ASSETS / "assets/img/lsmc-compact-white-transparent.png").read_bytes()
    ).decode("ascii")
    style = load_presentation()["style"]
    assert style["theme_icon"] == expected
    assert all(style["brand"][key] == expected for key in ("logo", "favicon"))
    assert style["brand"]["logo_dark"] == dark
    assert sorted(path.name for path in (ASSETS / "assets/img").glob("lsmc*.png")) == [
        "lsmc-compact-black-transparent.png", "lsmc-compact-white-transparent.png"
    ]


def test_clipboard_units_are_parser_extracted_text():
    content = (
        '<table id="units" class="mqc_per_sample_table"><thead><tr><th id="header_rate">Rate</th></tr>'
        '</thead><tbody><tr><td data-numeric-value="0.123456789" data-field-id="units/rate" '
        'data-numeric-suffix="&lt;span&gt;reads &amp;amp; bases&lt;/span&gt;">0.123456789</td></tr></tbody></table>'
    )
    _, tables = extract_tables(content)
    row = tables["units"]["rows"][0]
    assert row["numeric"][0]["suffix"] == "reads & bases"
    assert row["numeric"][0]["value"] == "0.123456789"
    assert row["precise"] == ["0.123456789"]
    assert "&lt;span&gt;" in row["html"]


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "inputs"
    source.mkdir()
    (source / "metrics_mqc.tsv").write_text(
        '# plot_type: "table"\n# section_name: "Precise metrics"\nSample\tValue\n'
        + "".join(f"sample-{n:03}\t{n + 0.123456789}\n" for n in range(123))
    )
    (source / "line_mqc.json").write_text(
        json.dumps(
            {
                "id": "fixture-line",
                "section_name": "Complete line",
                "plot_type": "linegraph",
                "pconfig": {"id": "fixture-line-plot", "title": "Scientific line"},
                "data": {"sample-001": {"1": 1.123456789, "2": 2.234567891}},
            }
        )
    )
    output = tmp_path / "output"
    result = multiqc.run(source, cfg=ClConfig(template="lsmc-paginated", output_dir=str(output), no_ai=True))
    assert result.sys_exit_code == 0
    manifest_path = output / "multiqc_report.bundle.json"
    return output, json.loads(manifest_path.read_text())


def page_data(path):
    encoded = re.search(r'atob\(("[^"]*")\)', path.read_text()).group(1)
    return json.loads(gzip.decompress(base64.b64decode(json.loads(encoded))))


def test_paginated_native_sections_and_complete_rows(bundle):
    root, manifest = bundle
    index = root / manifest["entry"]
    assert index.stat().st_size < 2_000_000
    assert len(manifest["pages"]) >= 3
    assert manifest["scientific_plot_ids"]
    assert set(manifest["scientific_plot_ids"]) == {p for page in manifest["pages"] for p in page["plots"]}
    counts = []
    for item in manifest["files"]:
        path = root / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        if path.suffix == ".html":
            html = BeautifulSoup(path.read_text(), "html.parser")
            assert not html.select("table[data-paginated-table] tbody tr")
            assert not html.select('script[type="module"]')
            for element in html.select("script[src], link[rel=stylesheet]"):
                resource = element.get("src", element.get("href"))
                assert (path.parent / resource).is_file(), resource
        if "/data/" in item["path"]:
            payload = page_data(path)
            counts.extend(len(table["rows"]) for table in payload["tables"].values())
    assert 123 in counts


def test_refresh_only_changes_presentation(bundle, tmp_path):
    root, manifest = bundle
    before = {item["path"]: item["sha256"] for item in manifest["files"]}
    context = tmp_path / "context.yaml"
    context.write_text('title: New introduction\nmarkdown: "**Evidence** <script>bad()</script>"\n')
    settings = tmp_path / "presentation.yaml"
    settings.write_text(
        f"report_context_file: {context.name}\nreport_links:\n  title: Files\n  items:\n    - label: Manifest\n      url: ./package_manifest.json\n"
    )
    result = CliRunner().invoke(
        main, ["refresh", "--config", str(settings), "--manifest", str(root / manifest["manifest_path"])]
    )
    assert result.exit_code == 0, result.output
    updated = json.loads((root / manifest["manifest_path"]).read_text())
    changed = [item["path"] for item in updated["files"] if before[item["path"]] != item["sha256"]]
    assert changed == [manifest["presentation_path"]]
    sidecar = (root / manifest["presentation_path"]).read_text()
    assert "New introduction" in sidecar
    assert "<script>" not in sidecar


@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "data:text/html,test", "//host/file", "/etc/passwd", "https://user:pass@host/path", " x "],
)
def test_unsafe_url_rejected(url):
    with pytest.raises(ValueError):
        safe_url(url)


def test_signed_url_unchanged():
    url = "https://example.test/a?X-Amz-Signature=a%2Fb%2Bc&X-Amz-Credential=x%2Fy"
    assert safe_url(url) == url


def test_context_conflict_and_dark_rejected(tmp_path, monkeypatch):
    config.reset()
    context = tmp_path / "context.yaml"
    context.write_text("title: Context\nmarkdown: Evidence\n")
    config.report_context_file = str(context)
    monkeypatch.setenv("MULTIQC_REPORT_CONTEXT", "{}")
    with pytest.raises(ValueError, match="not both"):
        load_presentation()
    monkeypatch.delenv("MULTIQC_REPORT_CONTEXT")
    config.report_context_file = None
    monkeypatch.setenv("MULTIQC_REPORT_STYLE", '{"default_theme":"dark"}')
    with pytest.raises(ValueError, match="Dark"):
        load_presentation()


def test_missing_configured_resource_is_error(tmp_path):
    config.reset()
    path = tmp_path / "config.yaml"
    path.write_text("report_context_file: missing.yaml\n")
    with pytest.raises(ValueError, match="path not found"):
        config.load_config_file(path)


def test_prepare_sharing_complete_mapping_preserves_signatures(bundle, tmp_path):
    root, manifest = bundle
    paths = [item["path"] for item in manifest["files"]] + [manifest["manifest_path"]]
    resources = {
        path: f"https://private.example.test/{path}?X-Amz-Signature=abc%2Bdef%2F123&X-Amz-Expires=604800"
        for path in paths
    }
    mapping = tmp_path / "signed.json"
    mapping.write_text(json.dumps({"resources": resources}))
    output = tmp_path / "shared"
    args = [
        "prepare-sharing",
        "--manifest",
        str(root / manifest["manifest_path"]),
        "--url-map",
        str(mapping),
        "--output-dir",
        str(output),
    ]
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output or str(result.exception)
    page = BeautifulSoup((output / manifest["entry"]).read_text(), "html.parser")
    for element in page.select("script[src],link[rel=stylesheet]"):
        assert element.get("src", element.get("href")) in resources.values()
    # The offline source was not changed.
    for item in manifest["files"]:
        assert hashlib.sha256((root / item["path"]).read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("digits", [0, 18, True, "6", 3.5])
def test_display_precision_rejects_invalid_digits(digits, monkeypatch):
    config.reset()
    monkeypatch.setenv("MULTIQC_REPORT_DISPLAY", json.dumps({"significant_digits": digits}))
    with pytest.raises(ValueError, match="Significant digits"):
        load_presentation()


def test_display_precision_is_separate_from_science(monkeypatch):
    config.reset()
    monkeypatch.setenv("MULTIQC_REPORT_DISPLAY", '{"significant_digits":6,"fields":{"table/coverage":8}}')
    payload = load_presentation()
    assert payload["display"] == {"significant_digits": 6, "fields": {"table/coverage": 8}}


@pytest.fixture
def sections():
    return [
        {"anchor": "general_stats", "title": "General Statistics", "modules": [], "general": True},
        *[
            {
                "anchor": name,
                "title": name,
                "modules": [SimpleNamespace(anchor="tool", sections=[name])],
                "general": False,
            }
            for name in ["first", "second"]
        ],
    ]


def test_group_modules_once_with_general_stats(sections):
    pages = group_pages(sections, [{"id": "qc", "title": "QC", "modules": ["tool"], "sections": ["general_stats"]}])
    assert len(pages) == 1
    assert pages[0]["general"]
    assert len(pages[0]["modules"]) == 1
    assert pages[0]["modules"][0].sections == ["first", "second"]
    assert sections[1]["modules"][0].sections == ["first"]
    assert [s["anchor"] for s in pages[0]["outputs"]] == ["general_stats", "first", "second"]


@pytest.mark.parametrize(
    "groups, error",
    [
        ([], "non-empty"),
        ([{"id": "bad/path", "title": "Bad"}], "slug"),
        ([{"id": "qc", "title": "QC", "modules": ["typo"]}], "Unknown modules"),
        ([{"id": "qc", "title": "QC", "sections": ["typo"]}], "Unknown sections"),
        ([{"id": "qc", "title": "QC", "sections": ["first", "first"]}], "Duplicate"),
        ([{"id": "qc", "title": "QC", "modules": ["tool"], "sections": ["first"]}], "more than once"),
        ([{"id": "qc", "title": "QC", "modules": ["tool"]}], "not assigned"),
        ([{"id": "qc", "title": "QC"}], "no outputs"),
        ([{"id": "qc", "title": "QC", "section": ["first"]}], "support only"),
        ([{"id": "qc", "title": "QC", "sections": "first"}], "list of exact"),
        (
            [{"id": "qc", "title": "QC", "sections": ["first"]}, {"id": "qc", "title": "QC", "sections": ["second"]}],
            "Duplicate report group",
        ),
        (
            [
                {"id": "qc", "title": "QC", "sections": ["first"]},
                {"id": "other", "title": "Other", "sections": ["first"]},
            ],
            "more than once",
        ),
    ],
)
def test_invalid_groups_fail_closed(sections, groups, error):
    with pytest.raises(ValueError, match=error):
        group_pages(sections, groups)


def test_grouped_render_retains_complete_table_models_and_plot_ids(bundle):
    root, previous = bundle
    sections = [p["anchor"] for p in previous["pages"] if p["anchor"] != "index"]
    settings = root.parent / "groups.yaml"
    settings.write_text(json.dumps({"report_groups": [{"id": "all_qc", "title": "All QC", "sections": sections}]}))
    output = root.parent / "grouped"
    result = multiqc.run(
        root.parent / "inputs",
        cfg=ClConfig(template="lsmc-paginated", output_dir=str(output), no_ai=True, config_files=[str(settings)]),
    )
    assert result.sys_exit_code == 0
    manifest = json.loads((output / "multiqc_report.bundle.json").read_text())
    assert len(manifest["pages"]) == 2
    assert manifest["pages"][1]["sections"] == sections
    assert manifest["scientific_plot_ids"] == previous["scientific_plot_ids"]
    assert manifest["pages"][1]["plots"] == previous["scientific_plot_ids"]
    page = BeautifulSoup((output / manifest["pages"][1]["path"]).read_text(), "html.parser")
    assert len(page.select('.mqc-group-tabs a[aria-current="page"]')) == 1
    assert page.select_one('.mqc-group-tabs a[aria-current="page"]').text == "All QC"
    assert all(a.has_attr("data-bundle-nav") for a in page.select(".side-nav .mqc-nav a"))
    assert not page.select("table[data-paginated-table] tbody tr")

    def tables(base, inventory):
        found = {}
        for item in inventory["files"]:
            if "/data/" in item["path"]:
                found.update(page_data(base / item["path"])["tables"])
        return found

    assert tables(output, manifest) == tables(root, previous)
