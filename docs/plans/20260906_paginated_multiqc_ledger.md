# Paginated MultiQC implementation and acceptance ledger

Controlling plan and ledger: this file. User approved implementation 2026-09-06.
Owner: primary Codex agent. Independent review: GPT-6 Astra, xhigh, fresh context.

## Scope and fixed decisions

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
| PAGE-02 | MultiQC | Cross-page state, full-data tables, deduplication | OPEN | feature_implementation | 2 | primary | Pending | | |
| CFG-01 | MultiQC | External context, styles, links and refresh utility | OPEN | feature_implementation | 3 | primary | Pending | | |
| PRECISION-01 | MultiQC | Runtime display precision and field-by-field numeric review of original/candidate and Inflection reports | IN_PROGRESS | feature_implementation | 3/6 | primary | User added 2026-09-06; display only, retain underlying data/exports/thresholds | | |
| UI-01 | MultiQC | Five themes, real LSMC mark, branding and print | OPEN | feature_implementation | 3 | primary | Pending | | |
| SHARE-01 | MultiQC | Offline bundle and complete signed URL-map preparation | OPEN | feature_implementation | 3 | primary | Pending | | |
| DAYOA-01 | DayOA | Explicit packaging config and Inflection resources | OPEN | feature_implementation | 4 | primary | Pending | | |
| TEST-01 | Both | Focused regression and negative tests | OPEN | contract_test | 5 | primary | Pending | | |
| REVIEW-01 | Both | Independent fresh-context Astra xhigh review | OPEN | contract_test | 5 | reviewer | Pending | | |
| LIVE-01 | MultiQC | Frozen ILMN-14 inputs and real generation rc=0 | OPEN | contract_test | 6 | primary | Pending | | |
| PARITY-01 | MultiQC | Every module/plot/table/warning/identity/export preserved | OPEN | contract_test | 6 | primary | Pending | | |
| BROWSER-01 | MultiQC | Chrome/Firefox/Safari file and HTTPS acceptance | OPEN | contract_test | 6 | primary | Pending | | |
| PERF-01 | MultiQC | 48/192 AU scaling and recorded performance targets | OPEN | contract_test | 6 | primary | Pending | | |
| DELIVERY-01 | Both | ZIP, preview, reproduction docs, committed ledgers | OPEN | feature_implementation | 7 | primary | Pending | | |

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
