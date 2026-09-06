# Paginated MultiQC development draft review

This is a development preview, not a scientifically validated report or release.
The original 48-AU analytical results and original MultiQC report are preserved.
Only report generation reads the existing staged FSx inputs. No scientific
workflow is invoked by the draft reproduction utility.

## Opening the draft

Extract the entire ZIP, then open `report-draft02/index.html` in Chrome. Keep its
`index_files/` and `index_data/` siblings in place. No application server is
required. Chrome local-file opening is checked; the complete Firefox, Safari
and HTTPS matrix is still pending.

Use the contents or left navigation to open one section. Large tables show 50
rows at a time. The GIAB table has 510 rows and 11 pages. Treat these counts as
draft inspection evidence, not a complete scientific-content reconciliation.

## Suggested first review

1. Review main navigation, section titles and report context placement.
2. Open GIAB Concordance. Check FDR, precision and recall readability.
3. Change table pages and search for a sample beyond the first 50 rows.
4. Test specimen, sample, AU and modality selectors while navigating sections.
5. Review the LSMC mark and retained theme choices.

## Numeric formatting

The draft requests six significant digits for non-integer numeric table values.
Exact integer counts remain exact. This is a display-only policy; underlying
scientific values and original scientific exports are not rewritten.

A report configuration can specify a browser-readable presentation override:

```yaml
report_display_file: display.yaml
```

```yaml
# display.yaml
significant_digits: 6
fields:
  giab_concordance-section-plot_table/FDR: 9
```

`null` retains native formatting. `MULTIQC_REPORT_DISPLAY` accepts the equivalent
JSON instead of the file. A file and its environment alternative conflict.
Refresh an existing offline bundle without regenerating scientific plots:

```bash
multiqc-presentation refresh --config report-config.yaml --manifest index.bundle.json
```

The generated JavaScript sidecar, not the original YAML or environment variable,
is read when the HTML opens. The full field-by-field numeric comparison is still
pending. Plot labels, tooltips and axes do not yet implement this override.

## Known unfinished work

- The index still exceeds the 2 MB acceptance target. Whole-report AI metadata
  remains duplicated across pages. Removing this duplication must preserve
  available content and avoid eager loading unrelated scientific data.
- Some native AI controls on the index have not been integrated.
- Full table copying/export behavior, grouping, column reordering, counts and
  filtering require exhaustive checks beyond the current browser spot checks.
- Original versus candidate numeric/content parity, dedicated Inflection report
  comparison, performance scaling to 192 AUs and print validation remain open.
- Per-AU Inflection integration is a separate isolated DayOA candidate. It is
  not deployed to existing controllers or production environments.
- A signed URL to the index alone cannot authorize sibling objects in private
  S3. This preview is delivered as a ZIP; complete URL-map preparation is a
  separate sharing capability under test.

Do not use this draft for clinical interpretation or as a validated delivery.
The controlling ledger records the remaining acceptance gates and evidence.
