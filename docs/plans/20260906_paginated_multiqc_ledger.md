# Paginated MultiQC implementation and acceptance ledger

Controlling plan and ledger: this file. User approved implementation 2026-09-06.
Owner: primary Codex agent. Independent review: GPT-6 Astra, xhigh, fresh context.

## Scope and fixed decisions

2026-09-06 amendment: the user requested pipeline-stage groups as configurable
tabs instead of individual subsection pages. See
`20260906T073317Z_pipeline_groups_ledger.md` for the implemented opt-in grouping,
existing-FSx 48-AU draft04, review fixes, exact comparison caveats and delivery.
This amendment does not close the full plan's outstanding acceptance gates.

Implement opt-in `lsmc-paginated`, preserving ordinary single-file reports and
all scientific content and exports. A compact main page indexes independently
loaded sections; general statistics has its own page. Tables show 50 rows with
full-data sorting/filtering/copy/download. Deduplicate presentation-only selector
records and membership without changing the DayOA v3 input contract. Preserve
cross-page selectors, deep links, browser history, warnings and precision.

Use `multiqc --config` with `report_context_file`, `report_style_file`, and
`report_links` (title and ordered items: label, url, optional description).
Context/style also accept mutually exclusive JSON environment inputs
`MULTIQC_REPORT_CONTEXT` and `MULTIQC_REPORT_STYLE`. A refresh utility updates
browser-readable sidecars without scientific regeneration. New resource paths
resolve against their config source. Links resolve against the report entry page,
do not imply copying, preserve external signatures, and reject executable schemes.
Missing explicit resources and malformed settings fail clearly.

LSMC is the default controlling design. Retain Original, LSMC, Light, NoSee,
Tacky; remove Dark. External configuration owns menu/order/availability/default,
switcher, tokens, typography, spacing, density, logos/favicon/links, extra CSS,
and explicit Tacky environment policy. Use real geometric LSMC artwork. Style
cannot change scientific thresholds or PASS/FAIL/NO_CALL meaning. Bundle assets.

DayOA adds explicit `hiomr2_inflection_multiqc_config` passed with `--config`,
including AU context/subset content, links, styles, Inflection homepage icon and
upper-right link/title. Keep source config/resources in the clone and delivered
URLs portable. Preserve full-cohort reports and scientific/package contracts.

Offline ZIP must open via file:// with no server, fetch dependency, service worker
or CDN. Sharing preparation accepts a complete explicit presigned URL mapping,
preserves signatures, rejects omissions, embeds no credentials and publishes
nothing. Referenced large files are not automatically copied.

Replay original ILMN-14 48-AU report on pclu-19074 from original staged inputs,
with frozen config/provenance and isolated candidate environment/fresh report
output. Recheck headnode state, record visits, acquire write lock for outputs.
Preserve scientific results, pinned clone and production environment. Do not
launch full production catalog, change controllers, update production pins,
merge, tag, or publish customer data.

## Gate 0 local baseline

- MultiQC original: `/Users/jmajor/projects/lsmc/MultiQC`, branch
  `codex/six-manifest-native-multiqc`, untracked `.coverage` and `.playwright-cli/`
  preserved. Fresh remote maximum annotated tag `1.36.dev0-lsmc.17`, peeled
  `7cb01ef4d3c262fbed3c35c2460b378febce487e`.
- Candidate: `/Users/jmajor/projects/lsmc/MultiQC-paginated-20260906`, branch
  `codex/paginated-multiqc-20260906`, clean upon creation.
- DayOA original: `/Users/jmajor/projects/lsmc/daylily-omics-analysis`, dirty
  AGENTS.md and pre-existing recovery ledger preserved. Fresh remote maximum
  annotated tag `16.0.79`, peeled `12a0bd995f4e51109b47ae310b6250d922be0610`.
- DayOA candidate: `/Users/jmajor/projects/lsmc/dayoa-inflection-multiqc-20260906`,
  branch `codex/inflection-multiqc-config-20260906`, clean upon creation.
- Baseline commands: git status --short --branch, git ls-remote --tags (version
  sorted by ref), git cat-file -t, git rev-parse tag^{}.
- Original source capsule:
  `/fsx/analysis_results/pclu-19074/pclu19074-run14-48au-full-ifx-r16057-20260902t140600z/daylily-omics-analysis`.
- Source report: `results/day/hg38/reports/DAY_final_multiqc.html`.
- Source staging: `results/day/hg38/reports/multiqc_inputs/final/`.
- S3 source root:
  `s3://lsmc-ssf-sequencing-data/derived/validations/betelgeuse/ilmn-cohorts/ILMN-14/pclu-19074/pclu19074-run14-48au-full-ifx-r16057-20260902t140600z/daylily-omics-analysis`.
- Prior planning measured 159155982-byte HTML, 48 AUs, 61731347-byte selector
  JSON with 17291 duplicate eligible records. Revalidate for acceptance.
- AWS profile lsmc, region us-west-2. No live system state assumed current.

## Control ledger

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| BASE-01 | Both | Isolated branches from current maximum annotated tags | SUCCESS | contract_test | 0 | primary | Baseline above | | User checkouts preserved |
| BASE-02 | MultiQC | Baseline tests, source/artwork/config inventory | IN_PROGRESS | contract_test | 0 | primary | Pending | | |
| PAGE-01 | MultiQC | Independent section exporter and compact index | IN_PROGRESS | feature_implementation | 1 | primary | Pending | | |
| PAGE-02 | MultiQC | Cross-page state, full-data tables, deduplication | IN_PROGRESS | feature_implementation | 2 | primary | Implemented candidate, fixture browser checks; complete real-data controls pending | | |
| CFG-01 | MultiQC | External context, styles, links and refresh utility | IN_PROGRESS | feature_implementation | 3 | primary | Candidate implementation and focused tests | | |
| PRECISION-01 | MultiQC | Runtime display precision and field-by-field numeric review of original/candidate and Inflection reports | IN_PROGRESS | feature_implementation | 3/6 | primary | User added 2026-09-06; display only, retain underlying data/exports/thresholds | | |
| UI-01 | MultiQC | Five themes, real LSMC mark, branding and print | IN_PROGRESS | feature_implementation | 3 | primary | Assets bundled; original config legacy-logo override found in first draft | | |
| SHARE-01 | MultiQC | Offline bundle and complete signed URL-map preparation | IN_PROGRESS | feature_implementation | 3 | primary | Fixture tests; real draft ZIP generated | | |
| DAYOA-01 | DayOA | Explicit packaging config and Inflection resources | IN_PROGRESS | feature_implementation | 4 | primary | DayOA candidate 3256fa62, 12 focused tests pass, production environment unchanged | | |
| TEST-01 | Both | Focused regression and negative tests | IN_PROGRESS | contract_test | 5 | primary | 35 and 78 Python tests, 18 JavaScript tests, 12 DayOA tests; remaining checks open | | |
| REVIEW-01 | Both | Independent fresh-context Astra xhigh review | IN_PROGRESS | contract_test | 5 | reviewer | Preliminary review found table/copy/plot precision issues; final review pending | | |
| LIVE-01 | MultiQC | Frozen ILMN-14 inputs and real generation rc=0 | SUCCESS | contract_test | 6 | primary | Draft01 rc=0, 164.06 s, 4,263 input files plus original report/configs hash-unchanged | | Existing inputs only; this row is generation proof, not scientific parity |
| PARITY-01 | MultiQC | Every module/plot/table/warning/identity/export preserved | OPEN | contract_test | 6 | primary | Pending | | |
| BROWSER-01 | MultiQC | Chrome/Firefox/Safari file and HTTPS acceptance | IN_PROGRESS | contract_test | 6 | primary | Chrome synthetic fixture only; real draft browser check next | | |
| PERF-01 | MultiQC | 48/192 AU scaling and recorded performance targets | ATTEMPTING_BUGFIX | contract_test | 6 | primary | First index about 5 MB, over target; repeated AI metadata and logos identified | Whole-report AI metadata and legacy logo embeds are copied into each page | |
| DELIVERY-01 | Both | ZIP, preview, reproduction docs, committed ledgers | IN_PROGRESS | feature_implementation | 7 | primary | Draft01 ZIP generated, private relay approved, download/browser check in progress | | |

Acceptance targets: initial index payload <=2 MB; usable index <=2 s; section
controls <=3 s; filter <=200 ms, on recorded hardware versus same-source baseline.
192-AU test must include quadratic pairwise growth, not just repeated markup.
Performance misses or incomplete parity fail acceptance. All science/source
artifacts remain outside git. No OPEN/IN_PROGRESS rows may be described as done.

## Execution evidence

2026-09-06: instructions and ledger SOP read, worktrees created; implementation
starting. No live work, original-file changes, or production changes performed.

2026-09-06 user scope addition: notify when a reviewable preview is available;
review both reports' content and rendered numeric fields against authoritative
underlying values. Identify excessive rounding, small nonzero values displayed
as zero, and distinct raw values collapsed to identical displays. Add an optional
report-level browser-loaded display-precision sidecar with per-field overrides,
included in presentation refresh; do not change scientific data, exported values,
QC thresholds, identities, dates, or receipt semantics. Preserve native formatting
when no override is configured. Preview and parity are not yet ready.

## Candidate checkpoint (2026-09-06)

The implementation is a development candidate, not an accepted release. The
next operation renders new HTML from existing staged 48-AU data on FSx. It does
not rerun the 48-AU scientific analysis, invoke DayOA targets, submit Slurm jobs,
change the historical clone, or regenerate analytical outputs. The user
explicitly reaffirmed this boundary and requested a first draft before complete
acceptance testing. Any draft must be labelled unvalidated.

Implemented candidate surfaces include independent section HTML/data, compact
index, 50-row full-data table model, selector-membership interning, offline
assets, context/style/links/display sidecars, refresh and signed-map preparation.
DayOA candidate supplies in-clone Inflection configuration and bundled artwork.
These surfaces remain IN_PROGRESS until real-data parity and browser gates pass.

Evidence collected so far:

- Focused MultiQC Python: 35 passed (`test_paginated_report.py` and
  `test_lsmc_report_ui.py`).
- Broader MultiQC regression: 78 passed, 4 skipped in 7.88 s
  (`test_lsmc_concordance_precision.py`, `test_output_options.py`,
  `test_plots.py`, `test_config_wizard.py`).
- JavaScript: 18 passed at the prior checkpoint; rebuilt/retested for this
  candidate before commit.
- DayOA presentation and existing packaging tests: 12 passed.
- Chrome local-file synthetic report: 50 DOM rows out of 123 complete rows;
  search found the last row. This is not a real-data/browser acceptance gate.
- Independent preliminary numeric review found 2,509 nonzero numeric cells
  displayed as zero in the original report. Full reproducible field-by-field
  audit and candidate comparison remain pending.
- Last observed source on pclu-19074: historical clone at 16.0.70 with nine
  modified tracked files. Preserve it as input-only, not a candidate checkout.
- Source report SHA-256:
  `020db58edd08ff337b909529bac151ca2bd769eb84f106a5e6032058c7ca4763`.
- Original selector manifest SHA-256:
  `c28f4028bdf4fb69449cadb8146b0ea326a81d39efa3e6bca8144e24d9013a90`.

Known unfinished acceptance work includes plot precision (tables have initial
runtime precision), exhaustive numeric/content parity, all full-table controls,
real 48-AU and 192-AU performance, Firefox/Safari/HTTPS/print verification,
candidate environment integration, final independent review, ZIP and preview.
No gate is terminalized based only on prototype tests. No release, production
adoption, customer-data publication, or full command catalog has occurred.

### First existing-FSx draft, 2026-09-06 06:56 UTC

Candidate commit `931cd2a8075ae50281f266f94e8ac94986963d61` was pushed only to
`codex/paginated-multiqc-20260906`, cloned into a fresh locked report-output root,
and installed in an isolated venv. It reuses read-only base dependencies from
the original MultiQC environment (Plotly 6.9.0, Kaleido 0.2.1), with new
presentation dependencies installed only in the venv. No production environment
files were uninstalled or changed. Candidate wheel SHA-256:
`1fa81460e159ef3484cbdc4c1826a870c034d0bf2d1bd366e8308dde938eec43`.

Root:
`/fsx/analysis_results/pclu-19074/ilmn14-multiqc-pagination-draft-20260906t064750z/`.
Report: `report-draft01/index.html`; receipt: `report-draft01/render-receipt.json`.
Persistent report-only tmux: `ilmn14-multiqc-pagination-validation-20260906`.

- MultiQC rc=0; rendering 164.0616 s; peak child RSS 2,425,412 KiB.
- 4,263 current FSx staged input files hashed before and after, unchanged.
- Original report, selector manifest and both input config hashes unchanged.
- 48 AUs detected; index plus 106 section pages, 101 scientific plot IDs,
  146 scientific export files and 376 bundle files inventoried.
- No DayOA, Snakemake or Slurm scientific jobs were invoked.
- This is UNVALIDATED_DRAFT, not content-parity or performance acceptance.
- Index is approximately 5 MB, exceeding the 2 MB acceptance target. Inspection
  identified 3.46 MB of repeated AI metadata and two 0.69 MB legacy logo embeds.
  Treat the performance row as ATTEMPTING_BUGFIX; no claim of completed targets.
- User explicitly approved the private S3 relay
  `s3://lsmc-ssf-sequencing-data/_codex_report_previews/ilmn14-pagination-20260906t064750z/`
  for retrieving the draft ZIP. Bucket public ACLs/policies are blocked and
  ignored/restricted. This is draft transfer, not production publication;
  relay objects are retained, no S3 deletion.

The first draft must not wait for exhaustive numeric and multi-browser gates.
Deliver it with explicit caveats, then continue those gates and remaining fixes.

### Corrected draft02 handoff, 2026-09-06 07:18 UTC

Browser inspection of draft01 caught global significant-digit formatting rounding
integer counts. Corrected the formatter to retain integers exactly and added
regression cases. The draft replay now explicitly uses the bundled geometric
LSMC mark, overriding the historical configuration's older JPEG. Corrected the
missing-resource alert target ID. These are renderer/presentation changes only.

Candidate code: `9d8a0611f0aacd8fb89c67caef402b44dbd3b1bd`.
Second candidate wheel SHA-256:
`166869749799e5f558bda7cef13574bf60c12d612992ee2a0437ade35aaa2115`.
No dependency changes to the original production environment.

- `report-draft02/render-receipt.json`: rc=0; 165.4318 s rendering;
  peak child RSS 2,307,884 KiB; 4,263 staged files and original report/configs
  hash-unchanged; zero scientific workflows launched.
- ZIP `ILMN-14_48AU_paginated_draft02.zip` SHA-256:
  `c134a215f9f6abff8bbc00c689b9764ca49a32ce49cd34133c6270108363eb4a`.
  FSx and downloaded Mac copies match; extraction and bundle manifest hashes
  verify successfully.
- Download command completed with rc=0, SSM receipt
  `c1faf903-10be-47a3-885a-7eb1939a9ad8`.
- Private relay object:
  `s3://lsmc-ssf-sequencing-data/_codex_report_previews/ilmn14-pagination-20260906t064750z/dyec-headnode-transfer/pclu-19074/20260906T071436Z-13bc8657fb18/ILMN-14_48AU_paginated_draft02.zip`.
- Mac ZIP: `output/ILMN-14_48AU_paginated_draft02.zip`; extracted entry:
  `output/ILMN-14_48AU_paginated_draft02/report-draft02/index.html`.
- Chrome 152 local-file spot checks on Apple M5, 32 GiB, macOS 26.5.2:
  index 1,068 DOM nodes, 48 AUs, 106 section links; a single observed load event
  at 93.9 ms. This is not a controlled performance acceptance measurement.
  The original report's automated open timed out at 30 s; no speedup ratio is
  claimed because complete comparable timing evidence is not available.
- GIAB section: 510 model rows, 50 DOM rows, 11 pages. Page navigation checked.
  351 visible integer cells compared with presentation-unit values, zero
  mismatches. Example 2,512,291,789 remains exact. FDR
  0.0006842177795077984 displays as 0.000684218 instead of the original 0.0.
  This is a spot check, not the requested exhaustive field-by-field comparison.
- No browser errors observed on the checked index/GIAB pages. Screenshots under
  `output/playwright/ilmn14-draft02-index.png` and `ilmn14-draft02-giab.png`.
- Latest focused tests: 35 Python passed; 18 JavaScript passed. DayOA candidate
  `3256fa62` has 12 focused tests passing and a clean isolated local worktree.
- Draft output-root write lock released after terminal rendering/packaging and
  verified download. Named tmux shell and interactive SSM shell were left open.

The index remains approximately 3.7 MB and therefore misses the 2 MB gate.
Full-report AI metadata duplication remains, along with the other documented
numeric/content, UI, Inflection, scaling, and browser acceptance work. See
`20260906_paginated_draft_review.md`. Draft delivery does not terminalize Gate 7
or the full objective. All rows are not terminal; implementation is incomplete.
