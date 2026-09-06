"""Prepare explicit signed mappings and verify one additive report publication.

Does not upload, delete, overwrite, or change AWS configuration. Actual upload
uses the AWS CLI after preparation succeeds. Signed URLs stay in ignored local
output files, not the durable ledger or git.
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
from botocore.config import Config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "verify"])
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--old-report", required=True)
    args = parser.parse_args()
    if not args.prefix.endswith("/"):
        raise ValueError("Destination prefix requires a trailing slash")
    source = args.source.resolve(strict=True)
    manifest = json.loads((source / "index.bundle.json").read_text())
    required = {item["path"] for item in manifest["files"]} | {manifest["manifest_path"]}
    if args.old_report in required:
        raise ValueError("Old report overlaps a new output")
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    credentials = session.get_credentials()
    if credentials is None or credentials.get_frozen_credentials().token:
        raise ValueError("Seven-day sharing requires non-session credentials")
    client = session.client("s3", config=Config(signature_version="s3v4"))
    old = client.head_object(Bucket=args.bucket, Key=args.prefix + args.old_report)
    old_identity = {key: old[key] for key in ["ContentLength", "ETag", "LastModified"]}
    old_identity["LastModified"] = old_identity["LastModified"].isoformat()
    targets = {args.prefix + name for name in required}
    existing = {}
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=args.bucket, Prefix=args.prefix):
        for item in page.get("Contents", []):
            if item["Key"] in targets:
                existing[item["Key"]] = item["Size"]
    receipt_path = args.work_dir / "publication.json"
    if args.phase == "prepare":
        if existing:
            raise ValueError(f"Refusing to overwrite existing target objects: {sorted(existing)}")
        args.work_dir.mkdir(parents=True, exist_ok=False)
        os.chmod(args.work_dir, 0o700)
        issued = datetime.now(timezone.utc)
        resources = {
            name: client.generate_presigned_url(
                "get_object", Params={"Bucket": args.bucket, "Key": args.prefix + name}, ExpiresIn=604800
            )
            for name in sorted(required)
        }
        map_path = args.work_dir / "signed-resources.json"
        map_path.write_text(json.dumps({"resources": resources, "links": {}}, indent=2))
        os.chmod(map_path, 0o600)
        executable = Path(__file__).resolve().parents[2] / ".venv/bin/multiqc-presentation"
        subprocess.run(
            [str(executable), "prepare-sharing", "--manifest", str(source / manifest["manifest_path"]),
             "--url-map", str(map_path), "--output-dir", str(args.work_dir / "prepared")],
            check=True,
        )
        prepared = args.work_dir / "prepared"
        files = sorted(path.relative_to(prepared).as_posix() for path in prepared.rglob("*") if path.is_file())
        if set(files) != required:
            raise ValueError("Prepared inventory differs from explicitly mapped resources")
        receipt = {
            "state": "PREPARED_NOT_UPLOADED", "source": str(source),
            "destination": f"s3://{args.bucket}/{args.prefix}",
            "entry_s3_uri": f"s3://{args.bucket}/{args.prefix}{manifest['entry']}",
            "entry_url": resources[manifest["entry"]],
            "signed_at_utc": issued.isoformat(), "expires_at_utc": (issued + timedelta(days=7)).isoformat(),
            "old_report": old_identity, "files": files,
            "object_count": len(files), "total_bytes": sum((prepared / name).stat().st_size for name in files),
            "writes": 0, "deletes": 0,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2))
        os.chmod(receipt_path, 0o600)
        print(json.dumps({key: receipt[key] for key in ["state", "entry_s3_uri", "object_count", "total_bytes", "expires_at_utc"]}))
    else:
        receipt = json.loads(receipt_path.read_text())
        if receipt["old_report"] != old_identity:
            raise ValueError("Original report identity changed during publication")
        prepared = args.work_dir / "prepared"
        expected = {args.prefix + name: (prepared / name).stat().st_size for name in required}
        if expected != existing:
            missing = sorted(set(expected) - set(existing))
            sizes = [key for key in expected.keys() & existing.keys() if expected[key] != existing[key]]
            raise ValueError(f"Remote inventory differs: missing={missing}; size_mismatch={sizes}")
        receipt.update(state="UPLOADED_INVENTORY_VERIFIED", verified_at_utc=datetime.now(timezone.utc).isoformat(),
                       verified_object_count=len(existing), verified_bytes=sum(existing.values()),
                       writes=len(existing), old_report_unchanged=True)
        receipt_path.write_text(json.dumps(receipt, indent=2))
        print(json.dumps({key: receipt[key] for key in ["state", "entry_s3_uri", "verified_object_count", "verified_bytes", "old_report_unchanged", "expires_at_utc"]}))


if __name__ == "__main__":
    main()
