from __future__ import annotations

from pathlib import Path

from multiqc.modules.giabconcordance.giabconcordance import MultiqcModule


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_giab_native_metrics_use_four_significant_digits() -> None:
    headers = MultiqcModule.metric_headers()
    assert {"Precision", "Sensitivity-Recall", "Fscore"} <= set(headers)
    assert {header["format"] for header in headers.values()} == {"{:.4g}"}

    source = (
        REPO_ROOT / "multiqc/modules/giabconcordance/giabconcordance.py"
    ).read_text(encoding="utf-8")
    for field in ("Specificity", "FDR", "PPV", "AllVarMeanDP"):
        block = source.split(f'"{field}":', 1)[1].split("},", 1)[0]
        assert '"format": "{:.4g}"' in block


def test_truvari_native_metrics_use_four_significant_digits() -> None:
    source_path = next(
        (REPO_ROOT / "multiqc/modules").glob("truvari/truvari.py")
    )
    source = source_path.read_text(encoding="utf-8")
    assert source.count('"format": "{:.4g}"') >= 7
    for field in ("precision", "recall", "f1", "gt_concordance"):
        block = source.split(f'bench_headers["{field}"] =', 1)[1].split(
            "}\n", 1
        )[0]
        assert '"format": "{:.4g}"' in block
