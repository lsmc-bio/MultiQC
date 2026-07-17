import csv
import math
import re
import statistics
from collections import defaultdict
from io import StringIO
from typing import DefaultDict, Dict, List, Mapping, Optional, Sequence, Union


REQUIRED_COLUMNS = frozenset({"sample", "rule", "s", "cpu_time", "snakemake_threads", "task_cost"})
Value = Union[int, float, str, bool, None]
MISSING_METRIC_TOKENS = {"", "NA"}


def aggregate_rule_name(rule: str) -> str:
    name = rule.strip()
    if not name:
        raise ValueError("Combined benchmark row has a blank rule")
    name = name.split("~", 1)[0]
    return re.sub(r"\.(?:\d+|\d+(?:-\d+)+)$", "", name)


def _number(value: str, column: str, line_number: int, filename: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Combined benchmark {column} must be numeric on line {line_number}: {filename}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(
            f"Combined benchmark {column} must be finite and nonnegative on line {line_number}: {filename}"
        )
    return parsed


def _threads(value: str, line_number: int, filename: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Combined benchmark snakemake_threads must be an integer on line {line_number}: {filename}"
        ) from exc
    if parsed <= 0:
        raise ValueError(f"Combined benchmark snakemake_threads must be positive on line {line_number}: {filename}")
    return parsed


def _optional_number(value: str, column: str, line_number: int, filename: str) -> Optional[float]:
    if value.strip().upper() in MISSING_METRIC_TOKENS:
        return None
    return _number(value, column, line_number, filename)


def _optional_threads(value: str, line_number: int, filename: str) -> Optional[int]:
    if value.strip().upper() in MISSING_METRIC_TOKENS:
        return None
    return _threads(value, line_number, filename)


def parse_combined_benchmarks(text: Optional[str], filename: str) -> List[Dict[str, Value]]:
    if text is None:
        raise ValueError(f"Could not read combined benchmark TSV: {filename}")
    reader = csv.DictReader(StringIO(text), delimiter="\t")
    if not reader.fieldnames:
        raise ValueError(f"Combined benchmark TSV has no header: {filename}")
    fieldnames = list(reader.fieldnames)
    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError(f"Combined benchmark TSV has duplicate column names: {filename}")
    missing = sorted(REQUIRED_COLUMNS - set(fieldnames))
    if missing:
        raise ValueError(f"Combined benchmark TSV is missing required column(s) {', '.join(missing)}: {filename}")

    parsed_rows: List[Dict[str, Value]] = []
    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"Combined benchmark line {line_number} has more fields than its header: {filename}")
        missing_values = [column for column in fieldnames if row[column] is None]
        if missing_values:
            raise ValueError(f"Combined benchmark line {line_number} has fewer fields than its header: {filename}")
        normalized = {
            "rule": str(row["rule"]),
            "s": str(row["s"]),
            "cpu_time": str(row["cpu_time"]),
            "snakemake_threads": str(row["snakemake_threads"]),
            "task_cost": str(row["task_cost"]),
            "source_row_shape": "sample_scoped",
        }
        rule = normalized["rule"]
        walltime_seconds = _number(normalized["s"], "s", line_number, filename)
        cpu_time_seconds = _optional_number(normalized["cpu_time"], "cpu_time", line_number, filename)
        threads = _optional_threads(normalized["snakemake_threads"], line_number, filename)
        task_cost = _optional_number(normalized["task_cost"], "task_cost", line_number, filename)
        parsed_rows.append(
            {
                **{column: str(row[column]) for column in fieldnames},
                **normalized,
                "aggregate_rule": aggregate_rule_name(rule),
                "walltime_hours": walltime_seconds / 3600.0,
                "observed_cpu_time_hours": cpu_time_seconds / 3600.0 if cpu_time_seconds is not None else None,
                "allocated_vcpu_time_hours": walltime_seconds * threads / 3600.0 if threads is not None else None,
                "task_cost": task_cost,
                "snakemake_threads": threads,
            }
        )
    if not parsed_rows:
        raise ValueError(f"Combined benchmark TSV has no data rows: {filename}")
    return parsed_rows


def _summary(values: List[float], prefix: str) -> Dict[str, Value]:
    if not values:
        return {
            f"{prefix}_rows": 0,
            f"{prefix}_sum": None,
            f"{prefix}_mean": None,
            f"{prefix}_median": None,
            f"{prefix}_min": None,
            f"{prefix}_max": None,
        }
    return {
        f"{prefix}_rows": len(values),
        f"{prefix}_sum": sum(values),
        f"{prefix}_mean": statistics.mean(values),
        f"{prefix}_median": statistics.median(values),
        f"{prefix}_min": min(values),
        f"{prefix}_max": max(values),
    }


def _value_as_float(row: Mapping[str, Value], column: str) -> float:
    value = row[column]
    if not isinstance(value, (int, float)):
        raise TypeError(f"Parsed combined benchmark column is not numeric: {column}")
    return float(value)


def _numeric_values(rows: Sequence[Mapping[str, Value]], column: str) -> List[float]:
    return [_value_as_float(row, column) for row in rows if row[column] is not None]


def aggregate_benchmarks(rows: Sequence[Mapping[str, Value]]) -> Dict[str, Dict[str, Value]]:
    grouped: DefaultDict[str, List[Mapping[str, Value]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["aggregate_rule"])].append(row)

    summaries: Dict[str, Dict[str, Value]] = {}
    for rule, rule_rows in sorted(grouped.items()):
        walltime = _numeric_values(rule_rows, "walltime_hours")
        observed_cpu = _numeric_values(rule_rows, "observed_cpu_time_hours")
        allocated_vcpu = _numeric_values(rule_rows, "allocated_vcpu_time_hours")
        costs = _numeric_values(rule_rows, "task_cost")
        summaries[rule] = {
            "executions": len(rule_rows),
            **_summary(walltime, "walltime_hours"),
            **_summary(observed_cpu, "observed_cpu_time_hours"),
            **_summary(allocated_vcpu, "allocated_vcpu_time_hours"),
            **_summary(costs, "task_cost_usd"),
        }
    return summaries


def metric_distributions(rows: Sequence[Mapping[str, Value]], metric: str) -> Dict[str, List[float]]:
    values: DefaultDict[str, List[float]] = defaultdict(list)
    for row in rows:
        if row[metric] is not None:
            values[str(row["aggregate_rule"])].append(_value_as_float(row, metric))
    return dict(sorted(values.items()))
