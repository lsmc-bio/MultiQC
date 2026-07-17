import pytest

from multiqc.modules.somalier.somalier import MultiqcModule


def test_somalier_source_label_keeps_assay_context() -> None:
    label = MultiqcModule.somalier_source_label(
        "/results/HG003.hiomrs_lr.na.somalier.samples.tsv",
        "HG003",
    )

    assert label == "hiomrs_lr.na"


def test_somalier_source_label_rejects_unexpected_filename() -> None:
    with pytest.raises(ValueError, match="Unexpected Somalier samples filename"):
        MultiqcModule.somalier_source_label("HG003.samples.tsv", "HG003")
