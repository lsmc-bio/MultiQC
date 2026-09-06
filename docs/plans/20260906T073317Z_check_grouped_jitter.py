"""Bounded investigation of existing categorical-sex scatter jitter differences.

Never changes a report or waives the strict bundle comparison failure.
"""

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from compare_paginated_bundles import inspect

parser = argparse.ArgumentParser()
parser.add_argument("reference", type=Path)
parser.add_argument("candidate", type=Path)
args = parser.parse_args()
old, new = inspect(args.reference), inspect(args.candidate)
evidence = {}
for key in ("peddy_sex_check_plot", "somalier_sex_check_plot"):
    left, right = old["plots"][key], copy.deepcopy(new["plots"][key])
    count = 0
    assert len(left["datasets"]) == len(right["datasets"])
    for a, b in zip(left["datasets"], right["datasets"]):
        assert len(a["points"]) == len(b["points"])
        for x, y in zip(a["points"], b["points"]):
            assert round(x["x"]) == round(y["x"]) in (0, 1, 2)
            assert abs(x["x"] - round(x["x"])) <= 0.05
            assert abs(y["x"] - round(y["x"])) <= 0.05
            y["x"] = x["x"]
            assert x == y
            count += 1
    assert left == right, "A non-jitter plot property changed"
    with (args.reference / "index_data" / f"{key}.txt").open() as handle:
        a_rows = list(csv.DictReader(handle, delimiter="\t"))
    with (args.candidate / "index_data" / f"{key}.txt").open() as handle:
        b_rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(a_rows) == len(b_rows)
    for a, b in zip(a_rows, b_rows):
        assert round(float(a["X"])) == round(float(b["X"]))
        b["X"] = a["X"]
        assert a == b, "A non-jitter export value changed"
    evidence[key] = {"points": count, "export_rows": len(a_rows), "only_categorical_x_jitter_changed": True}
print(json.dumps(evidence, indent=2))
