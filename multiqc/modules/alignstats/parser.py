import csv
import json
from io import StringIO
from pathlib import Path
from typing import Dict, Optional, Union, cast

AlignstatsValue = Union[int, float, str, bool, None]

NATIVE_MARKER_KEYS = {
    "MappedReads",
    "MappedReadsPct",
    "AlignedReadLengthMean",
    "InsertSizeMean",
    "WgsCoverageMean",
    "CapCoverageMean",
    "FilteredRecordsPct",
}

GENERIC_NATIVE_FILENAMES = {"report.json", "report.txt", "alignstats.json", "alignstats.txt"}


def parse_combo_tsv(text: Optional[str], filename: str) -> Dict[str, Dict[str, AlignstatsValue]]:
    if text is None:
        raise ValueError(f"Could not read AlignStats TSV: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if reader.fieldnames is None:
        raise ValueError(f"AlignStats TSV has no header: {filename}")
    sample_field = "Sample" if "Sample" in reader.fieldnames else "sample" if "sample" in reader.fieldnames else ""
    if not sample_field:
        raise ValueError(f"AlignStats TSV requires Sample or sample column: {filename}")
    rows: Dict[str, Dict[str, AlignstatsValue]] = {}
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


def parse_native_report(text: Optional[str], filename: str) -> Dict[str, AlignstatsValue]:
    if text is None:
        raise ValueError(f"Could not read AlignStats report: {filename}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AlignStats native report is not valid JSON-like output: {filename}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"AlignStats native report must be an object: {filename}")
    if not NATIVE_MARKER_KEYS.intersection(parsed):
        raise ValueError(f"AlignStats native report does not contain recognized AlignStats metrics: {filename}")
    nested = sorted(key for key, value in parsed.items() if not isinstance(value, (int, float, str, bool, type(None))))
    if nested:
        raise ValueError(f"AlignStats native report contains non-scalar field(s) {', '.join(nested)}: {filename}")
    return cast(Dict[str, AlignstatsValue], parsed)


def native_sample_name(filename: str, root: Optional[str], fallback: str) -> str:
    if filename.endswith(".alignstats.json"):
        sample = filename[: -len(".alignstats.json")]
    elif filename.endswith(".alignstats.txt"):
        sample = filename[: -len(".alignstats.txt")]
    elif filename in GENERIC_NATIVE_FILENAMES and root:
        sample = Path(root).name
    else:
        sample = fallback
    return sample or fallback
