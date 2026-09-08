"""Validated report presentation and offline sidecar refresh utilities."""

import base64
import copy
import hashlib
import json
import mimetypes
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

import bleach
import click
import markdown
import yaml
from bs4 import BeautifulSoup

from multiqc import config

ASSETS = Path(__file__).parents[1] / "templates" / "default"
THEMES = ("original", "lsmc", "light", "nosee", "tacky")


def safe_url(value: str) -> str:
    """Validate without normalizing or changing signed URL bytes."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("A report URL must be a nonempty string without surrounding whitespace")
    if any(ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Control characters and backslashes are forbidden in report URLs")
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"", "https", "http"} or value.startswith("//"):
        raise ValueError(f"Unsupported report URL scheme: {parsed.scheme!r}")
    if parsed.scheme and (not parsed.netloc or parsed.username is not None):
        raise ValueError("External report URLs require a host and must not contain credentials")
    if not parsed.scheme and value.startswith("/"):
        raise ValueError("Report-local URLs must be relative, not machine-absolute paths")
    return value


def _mapping(value, label: str, fields: set) -> dict:
    if not isinstance(value, dict) or set(value) - fields:
        raise ValueError(f"{label} must be a mapping with only these keys: {sorted(fields)}")
    return value


def _source(path, env: str):
    value = os.environ.get(env)
    if path is not None and value is not None:
        raise ValueError(f"Specify a file or {env}, not both")
    if value is not None:
        return json.loads(value), Path.cwd()
    if path is not None:
        source = Path(path)
        return yaml.safe_load(source.read_text(encoding="utf-8")), source.resolve().parent
    return None, Path.cwd()


def _asset(value: str, base: Path) -> str:
    source = Path(value)
    if not source.is_absolute():
        source = base / source
    if not source.is_file():
        raise FileNotFoundError(f"Configured presentation asset does not exist: {source}")
    mime = mimetypes.guess_type(source.name)[0]
    if mime not in {
        "image/png",
        "image/jpeg",
        "image/svg+xml",
        "image/webp",
        "image/x-icon",
        "image/vnd.microsoft.icon",
    }:
        raise ValueError(f"Unsupported presentation image: {source}")
    return f"data:{mime};base64,{base64.b64encode(source.read_bytes()).decode('ascii')}"


def load_presentation() -> dict:
    """Return a self-contained, validated presentation payload; no scientific data."""
    display, _ = _source(config.report_display_file, "MULTIQC_REPORT_DISPLAY")
    if display is None:
        display = {"significant_digits": None, "fields": {}}
    _mapping(display, "report display", {"significant_digits", "fields"})
    display.setdefault("significant_digits", None)
    display.setdefault("fields", {})
    if not isinstance(display["fields"], dict) or not all(
        isinstance(key, str) and "/" in key for key in display["fields"]
    ):
        raise ValueError("Display fields must map explicit table/column or plot/axis keys to significant digits")
    for value in [display["significant_digits"], *display["fields"].values()]:
        if value is not None and (type(value) is not int or not 1 <= value <= 17):
            raise ValueError("Significant digits must be null (native format) or an integer from 1 to 17")
    context, _ = _source(config.report_context_file, "MULTIQC_REPORT_CONTEXT")
    if context is not None:
        _mapping(context, "report context", {"title", "markdown"})
        if not isinstance(context.get("title"), str) or not isinstance(context.get("markdown"), str):
            raise ValueError("Report context requires string title and markdown")
        context = {
            "title": context["title"],
            "html": bleach.clean(
                markdown.markdown(context["markdown"], extensions=["tables"]),
                tags={
                    "p",
                    "a",
                    "strong",
                    "em",
                    "code",
                    "pre",
                    "ul",
                    "ol",
                    "li",
                    "h3",
                    "h4",
                    "blockquote",
                    "br",
                    "table",
                    "thead",
                    "tbody",
                    "tr",
                    "th",
                    "td",
                },
                attributes={"a": ["href", "title"]},
                protocols={"https", "http"},
                strip=True,
            ),
        }
    links = copy.deepcopy(config.report_links)
    if links is not None:
        _mapping(links, "report_links", {"title", "items"})
        if not isinstance(links.get("title"), str) or not isinstance(links.get("items"), list):
            raise ValueError("report_links requires title and items")
        for item in links["items"]:
            _mapping(item, "report link", {"label", "url", "description"})
            if not isinstance(item.get("label"), str) or not item["label"].strip():
                raise ValueError("Each report link requires a nonempty label")
            safe_url(item.get("url"))
            if "description" in item and not isinstance(item["description"], str):
                raise ValueError("Report link description must be a string")
    style = json.loads((ASSETS / "report-style.json").read_text(encoding="utf-8"))
    style["default_theme"] = config.lsmc_default_theme
    style["environment"] = config.lsmc_environment
    style["allow_tacky"] = config.lsmc_allow_tacky
    supplied, base = _source(config.report_style_file, "MULTIQC_REPORT_STYLE")
    if supplied is not None:
        _mapping(supplied, "report style", set(style))
        for key, value in supplied.items():
            if key in {"themes", "brand"}:
                if not isinstance(value, dict):
                    raise ValueError(f"style.{key} must be a mapping")
                for name, definition in value.items():
                    if name not in style[key]:
                        raise ValueError(f"Unknown style.{key} entry: {name}")
                    if key == "themes":
                        _mapping(definition, f"theme {name}", {"label", "mode", "tokens"})
                        style[key][name].update(definition)
                    else:
                        style[key][name] = definition
            else:
                style[key] = value
    if style["default_theme"] not in THEMES:
        raise ValueError("Invalid default theme; Dark has been removed")
    if (
        not isinstance(style["menu"], list)
        or not style["menu"]
        or len(set(style["menu"])) != len(style["menu"])
        or set(style["menu"]) - set(THEMES)
    ):
        raise ValueError("Theme menu must be a nonempty unique list of supported themes")
    if style["default_theme"] not in style["menu"]:
        raise ValueError("Default theme must be enabled in menu")
    for key in ("show_switcher", "allow_tacky"):
        if type(style[key]) is not bool:
            raise ValueError(f"style.{key} must be boolean")
    if (
        not isinstance(style["environment"], str)
        or not isinstance(style["tacky_restricted_environments"], list)
        or not all(isinstance(v, str) for v in style["tacky_restricted_environments"])
    ):
        raise ValueError("Style environment policy must contain strings")
    if not style["allow_tacky"] and style["environment"] in style["tacky_restricted_environments"]:
        style["menu"] = [name for name in style["menu"] if name != "tacky"]
    if style["default_theme"] not in style["menu"]:
        raise ValueError("Default theme is forbidden by the configured environment policy")
    for name, definition in style["themes"].items():
        if definition["mode"] not in {"light", "dark"} or not isinstance(definition["label"], str):
            raise ValueError(f"Invalid theme definition: {name}")
        if not isinstance(definition["tokens"], dict):
            raise TypeError("Theme tokens must be a mapping of CSS custom properties")
        for key, value in definition["tokens"].items():
            if (
                not re.fullmatch(r"--[a-z][a-z0-9-]*", key)
                or not isinstance(value, str)
                or any(c in value for c in "{};<>")
                or re.search(r"url\s*\(|expression\s*\(", value, re.IGNORECASE)
            ):
                raise ValueError(f"Invalid style token: {key}")
    brand = style["brand"]
    for key in ("logo", "logo_dark", "favicon"):
        value = brand[key]
        if value is not None:
            brand[key] = _asset(value, base)
    default_mark = _asset("assets/img/lsmc-logo.png", ASSETS)
    style["theme_icon"] = default_mark
    if brand["logo"] is None:
        brand["logo"] = _asset(config.custom_logo, Path.cwd()) if config.custom_logo else default_mark
    if brand["logo_dark"] is None:
        brand["logo_dark"] = _asset(config.custom_logo_dark, Path.cwd()) if config.custom_logo_dark else brand["logo"]
    if brand["favicon"] is None:
        brand["favicon"] = _asset(config.custom_favicon, Path.cwd()) if config.custom_favicon else default_mark
    if config.custom_logo_url and not (supplied and "url" in supplied.get("brand", {})):
        brand["url"] = config.custom_logo_url
    if brand["url"]:
        safe_url(brand["url"])
    if (
        not isinstance(brand["alt"], str)
        or not isinstance(brand["width"], int)
        or isinstance(brand["width"], bool)
        or not 16 <= brand["width"] <= 600
    ):
        raise ValueError("Brand requires string alt and width between 16 and 600")
    if not isinstance(style["css_files"], list) or not all(isinstance(p, str) for p in style["css_files"]):
        raise ValueError("style.css_files must be a list of paths")
    css_parts = []
    for value in style.pop("css_files"):
        source = Path(value)
        if not source.is_absolute():
            source = base / source
        css = source.read_text(encoding="utf-8")
        if re.search(r"@import|url\s*\(|</style", css, re.IGNORECASE):
            raise ValueError("Additional CSS must be self-contained (no @import, url(), or closing style tags)")
        css_parts.append(css)
    style["css"] = "\n".join(css_parts)
    return {
        "schema_version": "multiqc-presentation-v1",
        "context": context,
        "links": links,
        "style": style,
        "display": display,
    }


def script_json(value) -> str:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def write_payload(path: Path, value: dict) -> None:
    path.write_text(f"window.MQCPresentation={script_json(value)};\n", encoding="utf-8")


def update_manifest(root: Path, manifest: dict) -> None:
    for item in manifest["files"]:
        path = root / item["path"]
        item["bytes"] = path.stat().st_size
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / manifest["manifest_path"]).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def read_bundle(manifest: Path):
    root = manifest.resolve().parent
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != "multiqc-paginated-v1" or data.get("shared"):
        raise click.ClickException("Requires an offline multiqc-paginated-v1 bundle")
    declared = [item["path"] for item in data["files"]]
    if len(set(declared)) != len(declared):
        raise click.ClickException("Duplicate bundle resource")
    for path in [*declared, data["manifest_path"], data["presentation_path"], data["entry"]]:
        if Path(path).is_absolute() or not (root / path).resolve().is_relative_to(root):
            raise click.ClickException(f"Bundle path escapes report root: {path}")
    for item in data["files"]:
        source = root / item["path"]
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
            raise click.ClickException(f"Missing or modified bundle resource: {item['path']}")
    if data["presentation_path"] not in declared or data["entry"] not in declared:
        raise click.ClickException("Bundle entry and presentation must be inventoried")
    return root, data


@click.group()
def main():
    """Refresh a paginated report's presentation or prepare private-S3 links."""


@main.command("validate-config")
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def validate_config(config_path: Path):
    """Fail closed on unsupported/missing presentation resources before generation."""
    config.reset()
    config.load_config_file(config_path)
    load_presentation()
    click.echo("Presentation configuration valid (context, style, links, display precision)")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--manifest", type=click.Path(exists=True, path_type=Path), required=True)
def refresh(config_path: Path, manifest: Path):
    """Update only presentation sidecars, without reading scientific inputs."""
    config.reset()
    config.load_config_file(config_path)
    payload = load_presentation()
    root, data = read_bundle(manifest)
    prior = json.loads(
        (root / data["presentation_path"])
        .read_text(encoding="utf-8")
        .removeprefix("window.MQCPresentation=")
        .strip()
        .removesuffix(";")
    )
    requested = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(requested, dict):
        raise click.ClickException("Refresh configuration must be a mapping")
    for name, keys in {
        "context": {"report_context_file"},
        "style": {
            "report_style_file",
            "lsmc_default_theme",
            "lsmc_environment",
            "lsmc_allow_tacky",
            "custom_logo",
            "custom_logo_dark",
            "custom_logo_url",
            "custom_favicon",
        },
        "display": {"report_display_file"},
        "links": {"report_links"},
    }.items():
        if not (keys & set(requested)) and f"MULTIQC_REPORT_{name.upper()}" not in os.environ:
            payload[name] = prior[name]
    write_payload(root / data["presentation_path"], payload)
    update_manifest(root, data)
    click.echo(f"Updated presentation only: {root / data['presentation_path']}")


@main.command("prepare-sharing")
@click.option("--manifest", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--url-map", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--output-dir", type=click.Path(path_type=Path), required=True)
def prepare_sharing(manifest: Path, url_map: Path, output_dir: Path):
    """Prepare a separate bundle using explicit signed URLs. Never upload or sign."""
    root, data = read_bundle(manifest)
    mapping = _mapping(json.loads(url_map.read_text(encoding="utf-8")), "URL map", {"resources", "links"})
    resources = mapping.get("resources")
    links = mapping.get("links", {})
    if not isinstance(resources, dict) or not isinstance(links, dict):
        raise click.ClickException("URL map requires resources and optional links mappings")
    required = {item["path"] for item in data["files"]} | {data["manifest_path"]}
    if set(resources) != required:
        raise click.ClickException(
            f"Incomplete URL map; missing={sorted(required - set(resources))}; unknown={sorted(set(resources) - required)}"
        )
    for value in [*resources.values(), *links.values()]:
        safe_url(value)
        if urlsplit(value).scheme != "https":
            raise click.ClickException("Shared resource mappings must use explicit HTTPS URLs")
    if output_dir.exists() or output_dir.resolve().is_relative_to(root):
        raise click.ClickException("Sharing output must be a fresh directory outside the offline report root")

    def rewrite(value: str, source: str) -> str:
        if value in links:
            return links[value]
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith("//"):
            if "x-amz-signature=" in parsed.query.lower():
                raise click.ClickException(f"Supply an explicit links mapping for private resource: {value}")
            return value
        if not parsed.path:
            return value
        target = (root / source).parent / unquote(parsed.path)
        key = os.path.relpath(target.resolve(), root)
        if key not in resources:
            raise click.ClickException(f"Missing links mapping for {value!r} referenced by {source}")
        if parsed.query:
            raise click.ClickException(f"Local query URL needs an exact links mapping: {value}")
        return resources[key] + (f"#{parsed.fragment}" if parsed.fragment else "")

    rewritten = {}
    for item in data["files"]:
        path = item["path"]
        source = root / path
        if path.endswith(".html"):
            soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
            for element in soup.select("[src], [href]"):
                for attr in ("src", "href"):
                    if element.has_attr(attr):
                        element[attr] = rewrite(element[attr], path)
            # Generated inline font faces and the explicit bundle entry URL.
            for style in soup.find_all("style"):
                style.string = re.sub(
                    r'url\(["\']?([^"\')]+)["\']?\)',
                    lambda m, source=path: f'url("{rewrite(m[1], source)}")',
                    style.get_text(),
                )
            for script in soup.find_all("script", src=False):
                content = script.string or ""
                if content.startswith("window.MQCBundle="):
                    settings, tail = content.removeprefix("window.MQCBundle=").split(
                        ";window.callAfterDecompressed=", 1
                    )
                    settings = json.loads(settings)
                    settings["entry"] = resources[data["entry"]]
                    script.string = f"window.MQCBundle={script_json(settings)};window.callAfterDecompressed={tail}"
            rewritten[path] = str(soup)
        elif path == data["presentation_path"]:
            payload = json.loads(
                source.read_text(encoding="utf-8").removeprefix("window.MQCPresentation=").strip().removesuffix(";")
            )
            if payload["links"]:
                for item in payload["links"]["items"]:
                    item["url"] = rewrite(item["url"], data["entry"])
            if payload["context"]:
                soup = BeautifulSoup(payload["context"]["html"], "html.parser")
                for anchor in soup.select("a[href]"):
                    anchor["href"] = rewrite(anchor["href"], data["entry"])
                payload["context"]["html"] = str(soup)
            if payload["style"]["brand"]["url"]:
                payload["style"]["brand"]["url"] = rewrite(payload["style"]["brand"]["url"], data["entry"])
            rewritten[path] = f"window.MQCPresentation={script_json(payload)};\n"
        elif path.endswith(".css"):
            rewritten[path] = re.sub(
                r'url\(["\']?([^"\')]+)["\']?\)',
                lambda m, source_path=path: f'url("{rewrite(m[1], source_path)}")',
                source.read_text(encoding="utf-8"),
            )
    # All mapping/resource validation is completed before creating any output.
    output_dir.mkdir(parents=True)
    for item in data["files"]:
        path = item["path"]
        target = output_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if path in rewritten:
            target.write_text(rewritten[path], encoding="utf-8")
        else:
            shutil.copy2(root / path, target)
    data["shared"] = True
    update_manifest(output_dir, data)
    click.echo(f"Prepared only, nothing published: {output_dir / data['entry']}")
