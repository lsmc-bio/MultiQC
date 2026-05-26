from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_parser():
    parser_path = Path(__file__).resolve().parents[1] / "parser.py"
    spec = importlib.util.spec_from_file_location("ultima_parser_under_test", parser_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parse_sample_first_tsv = _load_parser().parse_sample_first_tsv


def test_parse_sample_first_tsv_requires_sample_first_column() -> None:
    rows = parse_sample_first_tsv(
        "Sample\trun_id\tobserved_outputs\tmissing_required_outputs\n"
        "602202.Z0157.FAKE_SAMPLE_1\t602202\t9\t0\n",
        "ultima_demux_summary_mqc.tsv",
    )

    assert rows["602202.Z0157.FAKE_SAMPLE_1"]["observed_outputs"] == "9"


def test_parse_sample_first_tsv_rejects_unsafe_sample() -> None:
    with pytest.raises(ValueError, match="Unsafe Ultima Sample"):
        parse_sample_first_tsv("Sample\trun_id\nR1\t602202\n", "ultima_run_inventory_mqc.tsv")

    with pytest.raises(ValueError, match="first column must be Sample"):
        parse_sample_first_tsv("run_id\tSample\n602202\t602202\n", "ultima_run_inventory_mqc.tsv")

    with pytest.raises(ValueError, match="Duplicate Ultima Sample"):
        parse_sample_first_tsv(
            "Sample\trun_id\n602202\t602202\n602202\t602202\n",
            "ultima_run_inventory_mqc.tsv",
        )
