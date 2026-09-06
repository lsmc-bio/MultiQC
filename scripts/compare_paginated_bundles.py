"""Compare grouping-only changes with an existing paginated reference bundle.

This is structural and data-payload regression evidence, not scientific sign-off.
"""

import argparse
import base64
import gzip
import hashlib
import json
import re
from pathlib import Path


def unpack(encoded):
    return json.loads(gzip.decompress(base64.b64decode(encoded)))


def inspect(root):
    manifest = json.loads((root / "index.bundle.json").read_text())
    tables, plots, records, groupings = {}, {}, {}, {}
    for entry in manifest["files"]:
        path = root / entry["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Bundle hash mismatch: {path}")
    for page in manifest["pages"]:
        path = root / page["path"]
        html = path.read_text()
        encoded = re.search(r'<script[^>]+id="mqc_compressed_plotdata"[^>]*>(.*?)</script>', html, re.DOTALL)
        data = unpack(encoded.group(1).strip())
        for key, value in data.items():
            if key in plots:
                raise ValueError(f"Duplicate plot {key} in {root}")
            plots[key] = value
    for entry in manifest["files"]:
        if "/data/" not in entry["path"]:
            continue
        text = (root / entry["path"]).read_text()
        payload = unpack(json.loads(re.search(r'atob\(("[^"]*")\)', text).group(1)))
        for key, value in payload["tables"].items():
            if key in tables:
                raise ValueError(f"Duplicate table {key} in {root}")
            tables[key] = value
        selector = payload["selectors"]
        for record in selector["records"]:
            key = record["MultiQCAnalysisID"]
            if key in records and records[key] != record:
                raise ValueError(f"Inconsistent selector record: {key}")
            records[key] = record
        for key, dimensions in selector["plot_groupings"].items():
            for dimension in dimensions:
                for group in dimension["groups"]:
                    group["members"] = selector["memberships"][group.pop("members_ref")]
            groupings[key] = dimensions
    exports = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in manifest["scientific_exports"]}
    return {
        "manifest": manifest,
        "tables": tables,
        "plots": plots,
        "records": records,
        "groupings": groupings,
        "exports": exports,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    old, new = inspect(args.reference), inspect(args.candidate)
    checks = {}
    for kind in ("tables", "plots", "records", "groupings"):
        checks[kind] = {
            "reference_count": len(old[kind]),
            "candidate_count": len(new[kind]),
            "missing": sorted(old[kind].keys() - new[kind].keys()),
            "extra": sorted(new[kind].keys() - old[kind].keys()),
            "changed": sorted(key for key in old[kind].keys() & new[kind].keys() if old[kind][key] != new[kind][key]),
        }
    old_sections = [p["anchor"] for p in old["manifest"]["pages"] if p["anchor"] != "index"]
    new_sections = [s for p in new["manifest"]["pages"] for s in p["sections"]]
    checks["sections_exactly_once"] = sorted(old_sections) == sorted(new_sections) and len(new_sections) == len(
        set(new_sections)
    )
    checks["scientific_export_paths_identical"] = set(old["exports"]) == set(new["exports"])
    checks["scientific_exports_byte_identical"] = [
        p for p in old["exports"] if old["exports"][p] == new["exports"].get(p)
    ]
    checks["scientific_exports_byte_changed"] = [
        p for p in old["exports"] if old["exports"][p] != new["exports"].get(p)
    ]
    checks["data_payload_rc"] = (
        0
        if checks["sections_exactly_once"]
        and checks["scientific_export_paths_identical"]
        and all(
            not checks[k][field]
            for k in ("tables", "plots", "records", "groupings")
            for field in ("missing", "extra", "changed")
        )
        else 1
    )
    checks["export_rc"] = int(
        not checks["scientific_export_paths_identical"] or bool(checks["scientific_exports_byte_changed"])
    )
    checks["rc"] = checks["data_payload_rc"] or checks["export_rc"]
    args.receipt.write_text(json.dumps(checks, indent=2))
    print(json.dumps({k: v for k, v in checks.items() if k != "scientific_exports_byte_identical"}, indent=2))
    return checks["rc"]


if __name__ == "__main__":
    raise SystemExit(main())
