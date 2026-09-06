# MultiQC 1.36.dev0-lsmc.18

## Summary

This LSMC fork release adds optional, server-free paginated MultiQC reports,
pipeline-stage tabs, externally configured presentation and table precision,
and the approved report-title/logo/sidebar layout. Ordinary single-file report
generation remains available. The grouped 48-AU review example was approved by
the user after generation from existing analytical results, without rerunning
the scientific analysis.

## Paginated reports and pipeline-stage tabs

- Select `--template lsmc-paginated` through the normal MultiQC CLI.
- Generate a main index, independent section/group HTML pages, shared assets,
  page-specific data, scientific exports and an integrity manifest.
- Load detailed data for the selected page, with plots initialized as they
  become visible. Inactive groups are not preloaded as a hidden giant report.
- Configure ordered `report_groups` using exact module and/or section anchors.
  A tab can contain multiple tool outputs. Every visible section must be
  assigned exactly once; unknown, duplicate, overlapping, empty or incomplete
  assignments fail with explicit errors.
- Keep native output order within each group and index every output on the
  overview. Omitting groups retains independent per-section pages.
- Preserve selector state, deep-linked outputs and browser Back/Forward state
  through navigation, including links into collapsed report-context panels.
- Render 50 table rows per page while keeping sorting, filtering, counts,
  copying and exports connected to the complete relevant table model.
- Deduplicate repeated selector membership structures and presentation records
  without changing the DayOA v3 input contract or scientific exports.

The approved example groups 106 sections into ten tabs: Raw Reads, Alignment,
Coverage, SNVs & Indels, SVs & CNVs, Specialized Calls, Identity & Contamination,
QC Metrics, Validation, and Provenance & Runtime, plus Overview.

## Report identity and branding

- Show the global report title above the stage tabs on the index and every
  section page, with the configured logo in the upper right.
- Show the current section/group title at the top of the left sidebar, with
  the Report index link immediately below it.
- Use the geometric LSMC mark instead of the earlier placeholder artwork.
- Retain Original, LSMC, Light, NoSee and Tacky themes. Remove Dark from the
  theme menu and accepted configuration; explicitly configured Dark is rejected
  and obsolete saved Dark preferences are reported and cleared.
- External style configuration controls theme definitions, enabled/menu order,
  default selection, switcher visibility, tokens, fonts, spacing, density,
  logos, favicon, image link and additional CSS. Tacky availability is governed
  by explicit environment policy.
- Embed configured branding assets so report viewing does not depend on the
  original logo website remaining available.

## External context, links and numeric display

Use the existing `multiqc --config report.yaml` entry point with:

- `report_context_file`: title and Markdown narrative, sanitized for rendering.
- `report_style_file`: presentation and branding configuration.
- `report_display_file`: table significant digits and per-field overrides.
- `report_links`: ordered labels, URLs and optional descriptions.

Corresponding JSON environment inputs are `MULTIQC_REPORT_CONTEXT`,
`MULTIQC_REPORT_STYLE` and `MULTIQC_REPORT_DISPLAY`. Supplying both a file and
its environment alternative is an error. Missing resources and malformed
configuration fail explicitly.

Display significant digits accept 1 through 17, or null for native formatting.
Per-field keys use explicit `table/column` identifiers. Integer counts remain
exact instead of being shortened to the configured significant-digit count.
Cell tooltips retain underlying and display-unit values. These controls change
presentation, not raw measurements, thresholds, receipt states or exports.
General plot-axis/tooltip precision coverage is not complete in this release.

Clipboard unit text is extracted by an HTML parser during generation, replacing
incomplete client-side regex stripping identified by the release CodeQL check.
Raw numeric values, precise exports and native table HTML are preserved.

The Links section supports report-relative files and external HTTP/HTTPS URLs.
Relative links resolve consistently against the report index. External query
strings, including signatures, are preserved; executable URL schemes are
rejected. Linking to a file does not copy it into the delivered bundle.

Update presentation without reparsing scientific inputs or regenerating plots:

```bash
multiqc-presentation refresh --config report.yaml --manifest output/index.bundle.json
```

Browsers consume generated sidecars on opening the report; they do not read
environment variables or arbitrary local YAML paths directly. Group membership
changes still require report generation.

## Offline use and private-S3 preparation

Extract the complete report folder and open its main HTML file. No application
server, required fetch, service worker or CDN is needed for offline viewing.
Keep the adjacent asset/data directories with the HTML pages.

```bash
multiqc --template lsmc-paginated --config report.yaml --outdir output existing_inputs/
multiqc-presentation prepare-sharing --manifest output/index.bundle.json \
  --url-map signed-resources.json --output-dir shared-output
```

Sharing preparation requires an explicit complete HTTPS resource mapping,
preserves signatures and rejects missing mappings. It creates a separate
prepared bundle; it does not sign URLs, upload objects or embed AWS credentials.
Private linked resources require explicit mappings too. A presigned index URL
alone does not authorize sibling objects. Full real-data HTTPS acceptance
remains pending.

## Recorded evidence

- Approved final header-layout example: 48 AUs, 106 sections, ten stage tabs,
  101 plot definitions and 56 table models, using existing ILMN-14 FSx results.
- Final draft generation: rc=0, 164.1842 seconds; 4,263 source inputs unchanged,
  zero scientific workflows launched. ZIP approximately 52 MiB.
- Grouped draft04 versus preceding draft02: all 121,999 stored numeric table
  cells and 17,303 selector records match. Of 101 plot definitions, 99 match
  exactly; the other two differ only in verified random categorical X jitter
  in Peddy and Somalier, not measured Y values, identities or sex categories.
- Chrome local-file checks reached all ten groups with expected plot counts,
  no observed resource errors and no HTTP(S) resource requests. Deep-link and
  Back/Forward selector restoration were checked. A rendered GIAB spot check
  covered 351 integer cells with zero rounding mismatches.
- Earlier focused checks recorded 51 Python tests, a separate 10-test
  configuration/comparison invocation and 21 JavaScript tests passing. These
  suites overlap and are not an additive total. Fresh-context grouping review
  findings were corrected before handoff.
- Final header-only changes were built and rendered but not tested, at the
  user's explicit request. No new local test suite was run for this release.

Scientific equivalence means the same meaningful measurements, identities,
units and statuses with useful precision, not byte-identical HTML. Timestamps,
layout and within-category jitter are not scientific differences. Hashes are
retained for provenance and transfer integrity.

## Known limitations and separate adoption gates

- The approximately 3.6 MiB example index exceeds the planned 2 MB target;
  further whole-report AI metadata deduplication and performance work remain.
- Exhaustive original-report versus candidate rendered-value parity, Parquet
  semantic parity, full plot precision and all full-data table controls have
  not completed acceptance.
- Firefox, Safari, HTTPS, print, 192-AU quadratic-scaling and complete browser
  timing/memory acceptance are still open. The Chrome observations above are
  functional evidence, not a universal performance guarantee.
- DayOA Inflection packaging integration is a separate candidate and is not
  released, pinned or deployed by this MultiQC release.
- No production command catalog, controller, workflow environment, analysis
  output or customer-data publication is changed by this release. The review
  report retains its development-draft provenance; no customer report ZIP is
  attached to this public source release.

Detailed implementation and evidence are retained in the timestamped
`docs/plans/` ledgers and `docs/markdown/paginated_groups.md`.
