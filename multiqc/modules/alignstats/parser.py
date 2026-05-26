from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Dict


def parse_combo_tsv(text: str | None, filename: str) -> Dict[str, Dict[str, object]]:
    if text is None:
        raise ValueError(f"Could not read AlignStats TSV: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if reader.fieldnames is None:
        raise ValueError(f"AlignStats TSV has no header: {filename}")
    sample_field = "Sample" if "Sample" in reader.fieldnames else "sample" if "sample" in reader.fieldnames else ""
    if not sample_field:
        raise ValueError(f"AlignStats TSV requires Sample or sample column: {filename}")
    rows: Dict[str, Dict[str, object]] = {}
    for row in reader:
        sample = row[sample_field]
        if not sample:
            raise ValueError(f"AlignStats TSV row missing sample: {filename}")
        if sample in rows:
            raise ValueError(f"Duplicate AlignStats sample in {filename}: {sample}")
        rows[sample] = {
            key: value
            for key, value in row.items()
            if key not in {sample_field, "sample", "Sample"} and value not in {None, ""}
        }
    return rows


def parse_native_report(text: str | None, filename: str) -> Dict[str, object]:
    if text is None:
        raise ValueError(f"Could not read AlignStats report: {filename}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AlignStats native report is not valid JSON-like output: {filename}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"AlignStats native report must be an object: {filename}")
    return parsed
