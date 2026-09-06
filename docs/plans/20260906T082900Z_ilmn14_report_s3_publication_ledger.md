# Approved 48-AU report S3 publication

User requested additive publication of the approved new report and its
sidecars beside the old S3-exported MultiQC report, plus a seven-day link.
Controlling ledger: this file. No analysis rerun, local/FSx deletion, S3
deletion, overwrite of old outputs, public ACL or AWS policy change.

## Gate 0

- Source is the approved local draft05 folder, preserved unchanged:
  `output/ILMN-14_48AU_grouped_draft05/report-draft05-grouped/`.
- Source renderer commit `fd1087f3571db53e6fa54c90b59cc5fa5c104b09`, not a
  newly regenerated report from release commit. It contains the approved header
  layout. The later lsmc.18 clipboard-unit correction does not change this
  already approved report. Sharing is prepared by released utility code.
- Origin is ILMN-14, 48 AUs. Old report confirmed with live S3 HeadObject:
  159155982 bytes, ETag `63db03987928a38ea47024a10e0363ce-4`, modified
  2026-09-06T00:12:01Z.
- Destination prefix:
  `s3://lsmc-ssf-sequencing-data/derived/validations/betelgeuse/ilmn-cohorts/ILMN-14/pclu-19074/pclu19074-run14-48au-full-ifx-r16057-20260902t140600z/daylily-omics-analysis/results/day/hg38/reports/`.
- Old entry is `DAY_final_multiqc.html`; new entry is `index.html` with
  `index_files/`, `index_data/` and `index.bundle.json` siblings. Live top-level
  listing has no conflicting index paths; exact target preflight still required.
- Source bundle has 184 declared files, 413006191 bytes, plus its manifest.
  Upload only the declared report bundle, not replay environment/provenance
  directories or the customer report ZIP in a public GitHub release.
- Profile `lsmc`, region `us-west-2`; credentials verified non-session so the
  explicit 604800-second URL lifetime is not shortened by session-token expiry.
- Local repo starts clean at released main `400f3de84`; publication ledger and
  helper use isolated `codex/ilmn14-report-s3-publication-20260906` branch.
- Local source upload does not touch `/fsx/analysis_results` or a controller.
  No DRA operation is required to copy these already downloaded report files.
- Signed mapping and URL receipt remain in ignored mode-restricted output
  files. Never commit signed URLs or AWS credentials.

| ID | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|
| S3-01 | Complete signed-resource preparation with no target collisions | SUCCESS | feature_implementation | user publication request | primary | prepare-sharing rc=0, 185 explicit resources, no pre-existing target objects | | Signed mappings prepared without publication |
| S3-02 | Additive upload and object/byte verification, old report preserved | SUCCESS | feature_implementation | user publication request | primary | AWS CLI upload rc=0; S3 has all 185 objects, 414366570 bytes | | Old report ETag, size and modification time unchanged |
| S3-03 | Check signed index and tab loading, return seven-day URL | SUCCESS | contract_test | delivery verification | primary | Signed index, Raw Reads (13 plots, 4 tables) and Validation (4 plots, 2 tables) load in Chrome | | No error banner or console errors; logos loaded |

Prepared local directory:
`output/ILMN-14_48AU_s3_publication_20260906T082900Z/prepared/`.
Signed resources issued 2026-09-06T08:30:51Z, expire 2026-09-13T08:30:51Z.
Source integrity was checked by the existing prepare-sharing utility. The
prepared output contains exactly all 185 mapped report resources. Signing
rewrites presentation URLs, not analytical values or scientific outputs.

Upload: additive `aws s3 cp --recursive`, explicit prepared folder and exact
existing report parent prefix, `--checksum-algorithm SHA256`, no deletion or
ACL/policy change. rc=0. Verification compared every expected object size and
the full 185-object/414366570-byte inventory against live S3 listing. This is
transfer evidence, not a fresh scientific-value comparison. Original report
identity is unchanged. Signed URLs are only in ignored local publication output.

## Delivery receipt

- All three publication rows terminal SUCCESS. User-requested additive report
  publication complete. This is not closure of the broader development-plan
  scientific or full cross-browser acceptance gates.
- Entry S3 URI is the destination prefix above plus `index.html`, a sibling of
  `DAY_final_multiqc.html`. All sidecars/data directories are alongside it.
- Earliest signed expiry: 2026-09-13T08:30:51Z (04:30:51 America/New_York).
  All 185 resource signatures use 604800 seconds, including section pages,
  scripts, styles, fonts and downloads. No AWS credentials are embedded.
- Playwright skill used for real signed-HTTPS delivery checks, not a scientific
  or regression suite. Index loaded; navigation to Raw Reads and Validation
  preserved selector-state fragments and signed query strings. Expected plot
  and table models were available, logo natural width positive, no presentation
  error banner and zero console errors. No claim that every group was opened.
- Original local report, FSx data and historical report objects preserved.
  No S3 delete, controller operation, infrastructure change, release/tag change,
  public customer-data upload or bucket-policy/ACL modification.
- Browser snapshots and private signed-resource map remain ignored locally.
  Durable receipt and read-only preparation/verification helper committed on
  `codex/ilmn14-report-s3-publication-20260906`, without signed URL strings.
