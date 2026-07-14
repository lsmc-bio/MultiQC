import argparse
import csv
import hashlib
import math
from pathlib import Path
from typing import List, Tuple


EXPECTED_HEADER = [
    "sample",
    "rule",
    "s",
    "h:m:s",
    "max_rss",
    "max_vms",
    "max_uss",
    "max_pss",
    "io_in",
    "io_out",
    "mean_load",
    "cpu_time",
    "hostname",
    "ip",
    "nproc",
    "cpu_efficiency",
    "instance_type",
    "region_az",
    "spot_cost",
    "snakemake_threads",
    "task_cost",
    "slurm_job_id",
    "slurm_partition",
    "slurm_alloc_cpus",
]
EXPECTED_REJECTED_LINES = {
    123,
    124,
    128,
    129,
    130,
    134,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    145,
    146,
    147,
    148,
    149,
}
EXPECTED_REJECTED_PREFIX = "results/day/hg38/benchmarks/"
EXPECTED_ACCEPTED_ROWS = 130


def parse_nonnegative_float(value: str, column: str) -> None:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{column} must be finite and nonnegative")


def validate_row(row: List[str]) -> None:
    values = dict(zip(EXPECTED_HEADER, row))
    if not values["sample"].strip() or not values["rule"].strip():
        raise ValueError("sample and rule must be nonempty")
    parse_nonnegative_float(values["s"], "s")
    for column in ("cpu_time", "task_cost"):
        if values[column].strip().upper() not in {"", "NA"}:
            parse_nonnegative_float(values[column], column)
    threads = values["snakemake_threads"].strip()
    if threads.upper() not in {"", "NA"} and int(threads) <= 0:
        raise ValueError("snakemake_threads must be positive")


def build(source: Path, output: Path, rejections: Path) -> Tuple[int, int]:
    lines = source.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Benchmark input is empty: {source}")
    header = next(csv.reader([lines[0]], delimiter="\t"))
    if header != EXPECTED_HEADER:
        raise ValueError(f"Unexpected benchmark header: {source}")

    accepted: List[List[str]] = []
    rejected: List[List[str]] = []
    for line_number, raw_text in enumerate(lines[1:], start=2):
        row = next(csv.reader([raw_text], delimiter="\t"))
        try:
            if len(row) != len(EXPECTED_HEADER):
                raise ValueError(f"field count {len(row)} does not match header count {len(EXPECTED_HEADER)}")
            validate_row(row)
        except (ValueError, TypeError) as exc:
            rejected.append(
                [str(source), str(line_number), str(exc), hashlib.sha256(raw_text.encode()).hexdigest(), raw_text]
            )
            continue
        accepted.append(row)

    if len(accepted) != EXPECTED_ACCEPTED_ROWS:
        details = "; ".join(f"line {row[1]}: {row[2]}" for row in rejected)
        raise ValueError(
            f"Expected {EXPECTED_ACCEPTED_ROWS} valid rows, found {len(accepted)}; rejections: {details}"
        )
    rejected_lines = {int(row[1]) for row in rejected}
    rejected_first_fields = [next(csv.reader([row[4]], delimiter="\t"))[0] for row in rejected]
    if rejected_lines != EXPECTED_REJECTED_LINES:
        raise ValueError(f"Rejected line set does not match the known shifted benchmark rows: {rejected_lines}")
    if not all(value.startswith(EXPECTED_REJECTED_PREFIX) for value in rejected_first_fields):
        raise ValueError("A rejected row is not one of the known unscoped benchmark-path rows")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(EXPECTED_HEADER)
        writer.writerows(accepted)
    with rejections.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["source_path", "line_number", "reason", "row_sha256", "raw_text"])
        writer.writerows(rejected)
    return len(accepted), len(rejected)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the validated HG003 1x canonical benchmark input")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rejections", required=True, type=Path)
    args = parser.parse_args()

    accepted, rejected = build(args.source, args.output, args.rejections)
    output_sha = hashlib.sha256(args.output.read_bytes()).hexdigest()
    rejection_sha = hashlib.sha256(args.rejections.read_bytes()).hexdigest()
    print(f"accepted_rows={accepted}")
    print(f"rejected_rows={rejected}")
    print(f"output_sha256={output_sha}")
    print(f"rejections_sha256={rejection_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
