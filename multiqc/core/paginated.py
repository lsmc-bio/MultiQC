"""Section-level native rendering for relocatable, offline report bundles."""

import copy
import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup

from multiqc import config, report
from multiqc.core import tmp_dir
from multiqc.core.presentation import script_json, update_manifest, write_payload
from multiqc.templates.default import load_dayoa_selector_manifest


def _strings(value, result: set):
    if isinstance(value, dict):
        for key, child in value.items():
            result.add(str(key))
            _strings(child, result)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _strings(child, result)
    elif isinstance(value, str):
        result.add(value)


def intern_memberships(groupings):
    """Deduplicate identical member arrays without changing identity or order."""
    definitions = []
    seen = {}
    packed = copy.deepcopy(groupings)
    for dimensions in packed.values():
        for dimension in dimensions:
            for group in dimension["groups"]:
                members = group.pop("members")
                key = tuple(members)
                if key not in seen:
                    seen[key] = len(definitions)
                    definitions.append(members)
                group["members_ref"] = seen[key]
    return packed, definitions


def extract_tables(content: str):
    """Keep native headers/cells, but move the complete row model out of the DOM."""
    soup = BeautifulSoup(content, "html.parser")
    tables = {}
    for table in soup.select("table.mqc_per_sample_table"):
        tbody = table.find("tbody", recursive=False)
        if tbody is None:
            continue
        rows = []
        for row in tbody.find_all("tr", recursive=False):
            sample = row.select_one(".th-sample-name")
            cells = row.find_all(["th", "td"], recursive=False)
            rows.append(
                {
                    "html": str(row),
                    "sample": sample.get("data-original-sn") if sample else None,
                    "group": row.get("data-sample-group"),
                    "secondary": "expandable-row-secondary" in row.get("class", []),
                    "values": [cell.get("data-sorting-val", cell.get_text(" ", strip=True)) for cell in cells],
                    "text": [cell.get_text(" ", strip=True) for cell in cells],
                    "numeric": [
                        {
                            "value": cell.get("data-numeric-value"),
                            "field": cell.get("data-field-id"),
                            "suffix": cell.get("data-numeric-suffix", ""),
                        }
                        for cell in cells
                    ],
                    "precise": [cell.get("data-numeric-value", cell.get_text(" ", strip=True)) for cell in cells],
                }
            )
        table_id = table["id"]
        tables[table_id] = {
            "rows": rows,
            "headers": [h.get_text(" ", strip=True) for h in table.select("thead tr:first-child th")],
            "columns": [h.get("id", "").removeprefix("header_") for h in table.select("thead tr:first-child th")],
        }
        table["data-paginated-table"] = table_id
        tbody.clear()
    return str(soup), tables


def group_pages(sections, groups):
    """Compose native outputs into strict, ordered groups without dropping sections."""
    if groups is None:
        return [{**s, "outputs": [{"anchor": s["anchor"], "title": s["title"]}], "description": ""} for s in sections]
    if not isinstance(groups, list) or not groups:
        raise ValueError("report_groups must be a non-empty list")
    by_anchor = {s["anchor"]: s for s in sections}
    if len(by_anchor) != len(sections):
        raise ValueError("Report has duplicate section anchors; cannot group unambiguously")
    module_ids = {str(m.anchor) for s in sections for m in s["modules"]}
    assigned, group_ids, pages = set(), set(), []
    for group in groups:
        if not isinstance(group, dict) or set(group) - {"id", "title", "description", "modules", "sections"}:
            raise ValueError("report_groups entries support only id, title, description, modules and sections")
        gid, title = group.get("id"), group.get("title")
        if not isinstance(gid, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", gid) or gid == "index":
            raise ValueError("Report group id must be a lowercase slug other than index")
        if gid in group_ids:
            raise ValueError(f"Duplicate report group id: {gid}")
        group_ids.add(gid)
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Report group {gid} requires a non-empty title")
        description = group.get("description", "")
        if not isinstance(description, str):
            raise TypeError(f"Report group {gid} description must be text")
        chosen = set()
        for key, available in (("modules", module_ids), ("sections", set(by_anchor))):
            requested = group.get(key, [])
            if not isinstance(requested, list) or any(not isinstance(value, str) for value in requested):
                raise ValueError(f"Report group {gid} {key} must be a list of exact anchors")
            if len(set(requested)) != len(requested):
                raise ValueError(f"Duplicate {key} selectors in report group {gid}")
            missing = set(requested) - available
            if missing:
                raise ValueError(f"Unknown {key} in report group {gid}: {sorted(missing)}")
            for selector in requested:
                matches = {
                    s["anchor"]
                    for s in sections
                    if (
                        s["anchor"] == selector
                        if key == "sections"
                        else any(str(m.anchor) == selector for m in s["modules"])
                    )
                }
                duplicate = matches & (chosen | assigned)
                if duplicate:
                    raise ValueError(f"Sections assigned more than once: {sorted(duplicate)}")
                chosen.update(matches)
        if not chosen:
            raise ValueError(f"Report group {gid} has no outputs")
        assigned.update(chosen)
        selected = [s for s in sections if s["anchor"] in chosen]
        # Merge each module's sections once so module wrappers and assets are not duplicated.
        modules = {}
        for section in selected:
            for module in section["modules"]:
                if module.anchor not in modules:
                    modules[module.anchor] = copy.copy(module)
                    modules[module.anchor].sections = []
                modules[module.anchor].sections.extend(module.sections)
        pages.append(
            {
                "anchor": gid,
                "title": title,
                "description": description,
                "modules": list(modules.values()),
                "general": any(s["general"] for s in selected),
                "outputs": [{"anchor": s["anchor"], "title": s["title"]} for s in selected],
            }
        )
    missing = set(by_anchor) - assigned
    if missing:
        raise ValueError(f"Sections not assigned to a report group: {sorted(missing)}")
    return pages


def write_paginated(report_path: Path, env, return_html=False):
    """Render native sections independently, never split an already-built report."""
    root = report_path.parent
    directory = root / f"{report_path.stem}_files"
    if directory.exists():
        raise FileExistsError(f"Paginated report assets already exist; choose a fresh filename: {directory}")
    directory.mkdir(parents=True)
    (directory / "sections").mkdir()
    (directory / "data").mkdir()
    assets = directory / "assets"
    assets.mkdir()
    source = tmp_dir.get_tmp_dir()
    asset_files = [
        "compiled/css/multiqc.min.css",
        "compiled/js/multiqc.min.js",
        "compiled/js/bundle-index.js",
        "assets/fonts/NunitoSans-LSMC.woff2",
        "assets/fonts/SourceSerif4-LSMC.woff2",
        *[
            f"assets/js/packages/{name}"
            for name in (
                "jquery-3.1.1.min.js",
                "jquery-ui.min.js",
                "jquery.tablesorter.min.js",
                "FileSaver.min.js",
                "jszip.min.js",
                "plotly-3.1.2.custom.min.js",
                "pako_inflate.min.js",
                "showdown.min.js",
            )
        ],
    ]
    copied = {}
    for name in asset_files:
        src = source / name
        dest = assets / src.name
        shutil.copy2(src, dest)
        copied[name] = dest
    extras = {}
    for module in report.modules:
        for kind in ("js", "css"):
            for path in getattr(module, kind, {}).values():
                src = Path(path)
                digest = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
                dest = assets / f"{digest}-{src.name}"
                shutil.copy2(src, dest)
                extras[str(src)] = dest
    for path in config.custom_css_files:
        src = Path(path)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
        dest = assets / f"{digest}-{src.name}"
        shutil.copy2(src, dest)
        extras[str(src)] = dest
    presentation_path = directory / "presentation.js"
    write_payload(presentation_path, report.presentation)
    manifest = load_dayoa_selector_manifest(config.dayoa_report_selectors) if config.dayoa_report_selectors else None
    identities = {"specimen": set(), "sample": set(), "analysis_unit": set()}
    fields = {
        "specimen": ("SPECIMEN_ID", "SPECIMEN_EUID"),
        "sample": ("SAMPLEID", "SAMPLE_EUID"),
        "analysis_unit": ("ANALYSIS_UNIT_UID", "ANALYSIS_UNIT_EUID"),
    }
    if manifest:
        for record in manifest["selector_records"]:
            for dimension, (id_field, euid_field) in fields.items():
                if record[id_field] or record[euid_field]:
                    identities[dimension].add(json.dumps([record[id_field], record[euid_field]], separators=(",", ":")))
    catalog = {key: sorted(values) for key, values in identities.items()}
    bundle_id = str(uuid.uuid4())
    pages = []
    if not config.skip_generalstats:
        pages.append({"anchor": "general_stats", "title": "General Statistics", "modules": [], "general": True})
    for module in report.modules:
        if module.hidden:
            continue
        for section in module.sections:
            if not section.print_section:
                continue
            clone = copy.copy(module)
            clone.sections = [section]
            pages.append(
                {
                    "anchor": str(section.anchor),
                    "title": f"{module.name}: {section.name}" if section.name else module.name,
                    "modules": [clone],
                    "general": False,
                }
            )
    pages = group_pages(pages, config.report_groups)
    for number, page in enumerate(pages):
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", page["anchor"])
        page["path"] = directory / "sections" / f"{number + 1:03}-{slug}.html"
    index_page = {
        "anchor": "index",
        "title": config.title or "MultiQC Report",
        "modules": [],
        "general": False,
        "path": report_path,
        "outputs": [],
        "description": "",
    }
    page_inventory = []
    original_cfg = SimpleNamespace(**vars(config))
    for page in [index_page, *pages]:
        target = page["path"]
        url = lambda p, parent=target.parent: Path(os.path.relpath(p, parent)).as_posix()
        proxy = SimpleNamespace(**vars(report))
        proxy.report_uuid = bundle_id
        proxy.modules = page["modules"]
        proxy.bundle_presentation_url = url(presentation_path)
        page_cfg = copy.copy(original_cfg)
        page_cfg.skip_generalstats = not page["general"]
        content = ""
        if page["general"]:
            content = env.get_template("general_stats.html").render(report=proxy, config=page_cfg)
        if page["modules"]:
            content += env.get_template("content.html").render(report=proxy, config=page_cfg)
        content, tables = extract_tables(content)
        parsed = BeautifulSoup(content, "html.parser")
        anchors = {element["id"] for element in parsed.select("[id]")}
        plots = {str(key): value for key, value in report.plot_data.items() if str(key) in anchors}
        names = set()
        _strings(plots, names)
        for table in tables.values():
            names.update(row["sample"] for row in table["rows"] if row["sample"] is not None)
        # HTML-only modules (for example FastQC canvases) also carry sample labels.
        for element in parsed.select("[data-original-sn], .fastqc_seq_content"):
            if element.get("data-original-sn"):
                names.add(element["data-original-sn"])
            if "fastqc_seq_content" in element.get("class", []):
                _strings(json.loads(element.get_text()), names)
        records = []
        groupings = {}
        if manifest:
            groupings = {key: value for key, value in manifest["plot_groupings"].items() if key in plots}
            _strings(groupings, names)
            records = [r for r in manifest["records"] if r["MultiQCAnalysisID"] in names]
        # The validated input remains unchanged. Eligible rows are references at runtime.
        packed_groups, memberships = intern_memberships(groupings)
        data = {
            "tables": tables,
            "selectors": {"records": records, "plot_groupings": packed_groups, "memberships": memberships},
        }
        data_path = directory / "data" / f"{target.stem}.js"
        data_path.write_text(
            "window.MQCPageData=JSON.parse(pako.inflate(Uint8Array.from(atob("
            + script_json(report.compress_json(data))
            + "),c=>c.charCodeAt(0)),{to:'string'}));\n",
            encoding="utf-8",
        )
        bundle = {
            "id": bundle_id,
            "entry": url(report_path),
            "is_index": page is index_page,
            "identities": catalog,
            "grouped": config.report_groups is not None,
            "active": page["anchor"],
        }
        proxy.plot_compressed_json = report.compress_json(plots)
        proxy.plot_data = plots
        proxy.some_plots_are_deferred = report.some_plots_are_deferred
        nav = [
            {
                "title": p["title"],
                "href": url(p["path"]),
                "anchor": p["anchor"],
                "description": p["description"],
                "outputs": p["outputs"],
            }
            for p in pages
        ]
        deps = {
            "css": [
                url(copied["compiled/css/multiqc.min.css"]),
                *[url(extras[str(p)]) for p in config.custom_css_files],
            ],
            "js": [
                url(copied["assets/js/packages/jquery-3.1.1.min.js"]),
                url(copied["assets/js/packages/pako_inflate.min.js"]),
            ],
        }
        if page is not index_page:
            deps["js"] += [
                url(copied[n])
                for n in asset_files
                if n.startswith("assets/js/packages/")
                and not n.endswith(("jquery-3.1.1.min.js", "pako_inflate.min.js"))
            ]
        deps["js"].append(url(data_path))
        deps["js"].append(
            url(copied["compiled/js/bundle-index.js" if page is index_page else "compiled/js/multiqc.min.js"])
        )
        for module in page["modules"]:
            for kind in ("js", "css"):
                deps[kind].extend(url(extras[str(p)]) for p in getattr(module, kind, {}).values())
        deps = {kind: list(dict.fromkeys(paths)) for kind, paths in deps.items()}
        html = env.get_template("paginated.html").render(
            report=proxy,
            config=page_cfg,
            bundle=bundle,
            content=content,
            navigation=nav,
            deps=deps,
            index=page is index_page,
            asset_root=url(assets),
            page=page,
        )
        target.write_text(html, encoding="utf-8")
        page_inventory.append(
            {
                "path": target.relative_to(root).as_posix(),
                "anchor": page["anchor"],
                "title": page["title"],
                "sections": [s["anchor"] for s in page["outputs"]],
                "plots": sorted(plots),
                "tables": {key: len(t["rows"]) for key, t in tables.items()},
                "record_ids": [r["MultiQCAnalysisID"] for r in records],
            }
        )
    bundle_manifest = {
        "schema_version": "multiqc-paginated-v1",
        "id": bundle_id,
        "entry": report_path.name,
        "manifest_path": f"{report_path.stem}.bundle.json",
        "presentation_path": presentation_path.relative_to(root).as_posix(),
        "pages": page_inventory,
        "report_groups": config.report_groups,
        "scientific_plot_ids": sorted(str(key) for key in report.plot_data),
        "files": [
            {"path": p.relative_to(root).as_posix()}
            for p in [report_path, *sorted(directory.rglob("*"))]
            if p.is_file()
        ],
    }
    update_manifest(root, bundle_manifest)
    return report_path.read_text(encoding="utf-8") if return_html else None


def finalize_bundle(report_path: Path, data_dir: Path | None, plots_dir: Path | None):
    """Inventory scientific exports after their final copy/zip, and index them."""
    root = report_path.parent
    manifest_path = root / f"{report_path.stem}.bundle.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    exports = []
    for directory in (data_dir, plots_dir):
        if directory is None:
            continue
        if directory.is_dir():
            exports.extend(p for p in sorted(directory.rglob("*")) if p.is_file())
        elif directory.with_suffix(".zip").is_file():
            exports.append(directory.with_suffix(".zip"))
    paths = [p.relative_to(root).as_posix() for p in exports]
    manifest["scientific_exports"] = paths
    manifest["files"].extend({"path": p} for p in paths)
    soup = BeautifulSoup(report_path.read_text(encoding="utf-8"), "html.parser")
    section = soup.new_tag("section", id="report-downloads")
    heading = soup.new_tag("h2")
    heading.string = "Scientific exports"
    section.append(heading)
    listing = soup.new_tag("ul")
    for path in [manifest["manifest_path"], *paths]:
        item = soup.new_tag("li")
        link = soup.new_tag("a", href=path)
        link.string = path
        item.append(link)
        listing.append(item)
    section.append(listing)
    soup.select_one("#report-contents").insert_after(section)
    report_path.write_text(str(soup), encoding="utf-8")
    update_manifest(root, manifest)
