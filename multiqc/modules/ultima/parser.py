from __future__ import annotations

import csv
from io import StringIO
from typing import Dict


def parse_sample_first_tsv(text: str | None, filename: str) -> Dict[str, Dict[str, object]]:
    if text is None:
        raise ValueError(f"Could not read Ultima TSV file: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if reader.fieldnames is None:
        raise ValueError(f"Ultima TSV file has no header: {filename}")
    if reader.fieldnames[0] != "Sample":
        raise ValueError(f"Ultima TSV first column must be Sample: {filename}")
    rows: Dict[str, Dict[str, object]] = {}
    for row in reader:
        sample = row["Sample"]
        if sample in {"", "R1", "R2", "metrics"}:
            raise ValueError(f"Unsafe Ultima Sample value in {filename}: {sample}")
        if sample in rows:
            raise ValueError(f"Duplicate Ultima Sample value in {filename}: {sample}")
        rows[sample] = {key: value for key, value in row.items() if key != "Sample"}
    return rows
