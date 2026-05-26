# Ultima And AlignStats Native Module Notes

Date: 2026-05-26

Controlling DayOA ledger:

```text
/Users/jmajor/projects/daylily/daylily-omics-analysis/docs/plans/20260526T074804Z_ultima_run_qc_native_multiqc_ledger.md
```

This fork implements two upstream-shaped modules:

- `ultima`: reads normalized `ur-qc` Ultima run-QC TSV summaries. It requires `Sample` as the first column and does not scan CRAM, BAM, or large bedGraph files.
- `alignstats`: reads AlignStats JSON-like key-value reports and combined TSV exports such as `alignstats_combo_mqc.tsv`.

The module work is intentionally generic. LSMC-specific report grouping remains in DayOA MultiQC config.

