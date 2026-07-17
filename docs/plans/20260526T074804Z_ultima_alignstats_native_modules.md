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

## 100 Percent Readiness Update

The fork now treats duplicate sample claims as a hard error instead of silently
overwriting them:

- `BaseMultiqcModule.add_data_source()` rejects duplicate sample names within
  the same module section when they point to different source files.
- Custom content rejects duplicate sample names within the same custom-data
  section, including config-provided data and merged `_mqc` files.
- The `ultima` and `alignstats` parsers reject duplicate `Sample` rows in their
  native TSV inputs.
- The `ultima` module registers data sources under section-scoped keys so the
  same sample can legitimately appear in inventory, demux, trimmer, quality,
  coverage, and contamination sections without colliding.

Focused tests cover the core data-source check, custom-content duplicate
rejection, and the Ultima / AlignStats parser duplicate checks. The synthetic
end-to-end path from `ur-qc` export to native `multiqc --module ultima --strict`
now succeeds with unique section-scoped samples.
