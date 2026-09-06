"""Render a draft from existing inputs, with before/after hashes and a receipt.

This utility never invokes a scientific workflow or creates staging inputs.
Acquire the applicable FSx output-root lock before calling it on a headnode.
"""

import argparse
import hashlib
import json
import os
import resource
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime, timezone
from pathlib import Path


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inventory(directory):
    records = []
    for root, dirs, files in os.walk(directory, followlinks=True):
        dirs.sort()
        for name in sorted(files):
            path = Path(root) / name
            if not path.is_file():
                raise ValueError(f"Missing or unsupported staged input: {path}")
            records.append(
                {"path": path.relative_to(directory).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}
            )
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-clone", required=True, type=Path)
    parser.add_argument("--staged-inputs", required=True, type=Path)
    parser.add_argument("--original-report", required=True, type=Path)
    parser.add_argument("--config", required=True, action="append", type=Path)
    parser.add_argument("--selectors", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-comment", required=True)
    args = parser.parse_args()
    source = args.source_clone.resolve(strict=True)
    candidate = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=candidate, text=True).strip()
    if commit != args.candidate_commit:
        raise ValueError(f"Candidate commit differs: {commit}")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=candidate):
        raise ValueError("Candidate checkout is dirty")
    out = args.output_dir.resolve()
    if out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError("Draft output must not overlap the original analysis clone")
    args.staged_inputs = args.staged_inputs.resolve(strict=True)
    configs = [path.resolve(strict=True) for path in args.config]
    original = args.original_report.resolve(strict=True)
    selectors = args.selectors.resolve(strict=True)
    for path in [args.staged_inputs, original, selectors, *configs]:
        if not path.is_relative_to(source):
            raise ValueError(f"Input is outside the explicitly supplied source clone: {path}")
    out.mkdir(parents=True, exist_ok=False)
    provenance = out / "provenance"
    provenance.mkdir()
    initial = {str(path): digest(path) for path in [original, selectors, *configs]}
    print("Hashing existing staged report inputs; no analytical execution", flush=True)
    inputs = inventory(args.staged_inputs)
    (provenance / "inputs.before.json").write_text(json.dumps(inputs, indent=2))
    (provenance / "source-files.before.json").write_text(json.dumps(initial, indent=2))
    (provenance / "source.diff").write_bytes(subprocess.check_output(["git", "diff", "HEAD"], cwd=source))
    (provenance / "source.status").write_bytes(subprocess.check_output(["git", "status", "--porcelain"], cwd=source))
    (provenance / "environment.txt").write_bytes(subprocess.check_output([sys.executable, "-m", "pip", "freeze"]))
    command = [sys.executable, "-m", "multiqc", "--strict", "--no-version-check"]
    for path in configs:
        command.extend(["--config", str(path)])
    for setting in [
        f"dayoa_report_selectors: {json.dumps(str(selectors))}",
        "lsmc_default_theme: lsmc",
        "lsmc_service: LSMC Genomic Analysis QC",
        "lsmc_environment: internal",
        "lsmc_allow_tacky: false",
    ]:
        command.extend(["--cl-config", setting])
    for pattern in ["*/other_reports/logs/*", "other_reports/logs/*", "*_mqc.log"]:
        command.extend(["--ignore", pattern])
    command.extend(
        [
            "--template",
            "lsmc-paginated",
            "--filename",
            "index.html",
            "--outdir",
            str(out),
            "--title",
            args.title,
            "--comment",
            args.source_comment,
            str(args.staged_inputs),
        ]
    )
    presentation_env = {
        "MULTIQC_REPORT_CONTEXT": json.dumps(
            {
                "title": "Development draft: not yet validated",
                "markdown": "This paginated report reuses existing analytical results. No scientific workflows were rerun. "
                "Content and numeric parity, plot precision, browser compatibility and performance acceptance "
                "are still under review. The original report and scientific results are unchanged.",
            }
        ),
        "MULTIQC_REPORT_DISPLAY": json.dumps({"significant_digits": 6, "fields": {}}),
    }
    for key in presentation_env:
        if key in os.environ:
            raise ValueError(f"Unexpected presentation environment override: {key}")
    (provenance / "command.json").write_text(
        json.dumps({"cwd": str(source), "argv": command, "presentation_environment": presentation_env}, indent=2)
    )
    print(shlex.join(command), flush=True)
    started = datetime.now(UTC).isoformat()
    before = time.monotonic()
    with (out / "render.log").open("w") as log:
        result = subprocess.run(
            command, cwd=source, env={**os.environ, **presentation_env}, stdout=log, stderr=subprocess.STDOUT
        )
    elapsed = time.monotonic() - before
    final = {str(path): digest(path) for path in [original, selectors, *configs]}
    after_inputs = inventory(args.staged_inputs)
    (provenance / "inputs.after.json").write_text(json.dumps(after_inputs, indent=2))
    unchanged = initial == final and inputs == after_inputs
    receipt = {
        "started_utc": started,
        "completed_utc": datetime.now(UTC).isoformat(),
        "candidate_commit": commit,
        "multiqc_rc": result.returncode,
        "render_seconds": elapsed,
        "peak_child_rss_kib_linux": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "source_inputs_unchanged": unchanged,
        "input_file_count": len(inputs),
        "scientific_workflows_launched": 0,
        "acceptance": "UNVALIDATED_DRAFT",
        "output_files": [
            {"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size}
            for p in sorted(out.rglob("*"))
            if p.is_file()
        ],
    }
    (out / "render-receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({key: value for key, value in receipt.items() if key != "output_files"}, indent=2), flush=True)
    return result.returncode if unchanged else 2


if __name__ == "__main__":
    sys.exit(main())
