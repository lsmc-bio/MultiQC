import csv
from io import StringIO
from typing import Dict, Optional


def parse_sample_first_tsv(text: Optional[str], filename: str) -> Dict[str, Dict[str, str]]:
    if text is None:
        raise ValueError(f"Could not read Ultima TSV file: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if reader.fieldnames is None:
        raise ValueError(f"Ultima TSV file has no header: {filename}")
    if reader.fieldnames[0] != "Sample":
        raise ValueError(f"Ultima TSV first column must be Sample: {filename}")
    rows: Dict[str, Dict[str, str]] = {}
    for row in reader:
        sample = row["Sample"]
        if sample in {"", "R1", "R2", "metrics"}:
            raise ValueError(f"Unsafe Ultima Sample value in {filename}: {sample}")
        if sample in rows:
            raise ValueError(f"Duplicate Ultima Sample value in {filename}: {sample}")
        missing = sorted(key for key, value in row.items() if value is None)
        if missing:
            raise ValueError(f"Ultima TSV row has missing field(s) {', '.join(missing)}: {filename}")
        rows[sample] = {key: str(value) for key, value in row.items() if key != "Sample"}
    return rows
