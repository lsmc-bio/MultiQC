#!/usr/bin/env python3
"""Build a DayOA MultiQC config that delegates migrated inputs to native modules."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml


MIGRATED_CUSTOM_KEYS = frozenset(
    {
        "alignstats_combo",
        "alignstats_gs",
        "input_sample_libraries",
        "input_samples",
        "input_units",
        "reported_vs_inferred_sex_check",
        "rules_benchmark_data",
    }
)

# alignstats_gs was never explicitly ordered; all other migrated sections were.
EXPECTED_MODULE_ORDER_KEYS = MIGRATED_CUSTOM_KEYS - {"alignstats_gs"}
EXPECTED_REPORT_ORDER_KEYS = MIGRATED_CUSTOM_KEYS - {"alignstats_gs"}


def _mapping(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected {key!r} to be a mapping")
    return value


def _exact_present(container: set[str], expected: frozenset[str], context: str) -> None:
    missing = expected - container
    if missing:
        raise ValueError(f"Missing expected migrated keys in {context}: {sorted(missing)}")


def build_native_config(source: Path, output: Path, canonical_benchmarks: Path, analysis_root: Path) -> str:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("MultiQC configuration root must be a mapping")

    custom_data = _mapping(data, "custom_data")
    search_patterns = _mapping(data, "sp")

    # MultiQC 1.36 validates table plot configuration strictly. DayOA's live
    # config carries this legacy field in the plot-level config even though
    # `format` is only valid for individual table headers.
    giab_concordance = custom_data.get("giab_concordance")
    if not isinstance(giab_concordance, dict):
        raise ValueError("Expected custom_data.giab_concordance to be a mapping")
    giab_pconfig = giab_concordance.get("pconfig")
    if not isinstance(giab_pconfig, dict) or giab_pconfig.get("format") != "{:.4f}":
        raise ValueError("Expected legacy custom_data.giab_concordance.pconfig.format to be '{:.4f}'")
    del giab_pconfig["format"]

    _exact_present(set(custom_data), MIGRATED_CUSTOM_KEYS, "custom_data")
    _exact_present(set(search_patterns), MIGRATED_CUSTOM_KEYS, "sp")
    for key in MIGRATED_CUSTOM_KEYS:
        del custom_data[key]
        del search_patterns[key]

    staged_custom_root = analysis_root / "reports" / "multiqc_inputs" / "final" / "other_reports"
    custom_path_filters: list[str] = []
    for key, pattern in search_patterns.items():
        if not isinstance(pattern, dict) or not isinstance(pattern.get("fn"), str):
            raise ValueError(f"Expected sp.{key}.fn to be a string")
        filename_pattern = pattern["fn"]
        if filename_pattern.startswith("other_reports/"):
            custom_path_filters.append(str(staged_custom_root / filename_pattern.removeprefix("other_reports/")))
        else:
            custom_path_filters.append(str(analysis_root / filename_pattern))
    if not custom_path_filters:
        raise ValueError("No custom-content path filters remain after native migration")

    module_order = data.get("module_order")
    if not isinstance(module_order, list) or not all(isinstance(item, str) for item in module_order):
        raise ValueError("Expected module_order to be a list of strings")
    module_order_keys = set(module_order)
    _exact_present(module_order_keys, EXPECTED_MODULE_ORDER_KEYS, "module_order")
    unexpected_ordered = module_order_keys & (MIGRATED_CUSTOM_KEYS - EXPECTED_MODULE_ORDER_KEYS)
    if unexpected_ordered:
        raise ValueError(f"Unexpected migrated module_order keys: {sorted(unexpected_ordered)}")
    filtered_module_order: list[str | dict[str, dict[str, list[str]]]] = []
    for item in module_order:
        if item in MIGRATED_CUSTOM_KEYS:
            continue
        if item == "custom_content":
            filtered_module_order.append({item: {"path_filters": custom_path_filters}})
        elif item == "ganon":
            filtered_module_order.append(
                {
                    item: {
                        "path_filters": [str(analysis_root / "**" / "*.ganon2.multiqc.log")],
                    }
                }
            )
        else:
            filtered_module_order.append(item)
    custom_content_index = next(
        index
        for index, item in enumerate(filtered_module_order)
        if isinstance(item, dict) and "custom_content" in item
    )
    filtered_module_order.insert(
        custom_content_index,
        {
            "snakemake_benchmarks": {
                "path_filters": [str(canonical_benchmarks)],
            }
        },
    )
    data["module_order"] = filtered_module_order

    report_section_order = _mapping(data, "report_section_order")
    report_order_keys = set(report_section_order)
    _exact_present(report_order_keys, EXPECTED_REPORT_ORDER_KEYS, "report_section_order")
    unexpected_report_order = report_order_keys & (MIGRATED_CUSTOM_KEYS - EXPECTED_REPORT_ORDER_KEYS)
    if unexpected_report_order:
        raise ValueError(f"Unexpected migrated report_section_order keys: {sorted(unexpected_report_order)}")
    for key in EXPECTED_REPORT_ORDER_KEYS:
        del report_section_order[key]

    for section_name in ("custom_data", "sp", "report_section_order"):
        remaining = set(_mapping(data, section_name)) & MIGRATED_CUSTOM_KEYS
        if remaining:
            raise AssertionError(f"Migrated keys remain in {section_name}: {sorted(remaining)}")
    remaining_module_order = {item for item in data["module_order"] if isinstance(item, str)} & MIGRATED_CUSTOM_KEYS
    if remaining_module_order:
        raise AssertionError(f"Migrated keys remain in module_order: {sorted(remaining_module_order)}")

    rendered = (
        "# Generated for the HG003 1x whole-tree native-module render.\n"
        "# Legacy custom sections owned by native modules and one invalid table field were removed.\n"
        + yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--canonical-benchmarks", required=True, type=Path)
    parser.add_argument("--analysis-root", required=True, type=Path)
    args = parser.parse_args()
    digest = build_native_config(args.source, args.output, args.canonical_benchmarks, args.analysis_root)
    print(f"source={args.source}")
    print(f"output={args.output}")
    print(f"sha256={digest}")
    print(f"canonical_benchmarks={args.canonical_benchmarks}")
    print(f"analysis_root={args.analysis_root}")
    print(f"removed={','.join(sorted(MIGRATED_CUSTOM_KEYS))}")


if __name__ == "__main__":
    main()
