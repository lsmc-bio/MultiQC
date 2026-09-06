# Pipeline-stage grouped report draft

Controlling amendment to `20260906_paginated_multiqc_ledger.md`.
User requested configurable groups as tabs and a new existing-data 48-AU example.
Owner: primary agent. No release or scientific workflow execution authorized here.

## Gate 0

- Candidate branch `codex/paginated-multiqc-20260906`, clean at
  `429c677d96d7acae7ff8c92eb5e53445cff47456`.
- Preserve draft02 and the historical ILMN-14 FSx analysis clone unchanged.
- Draft02 manifest: 106 individual sections, 101 plot definitions, 146 exports.
- Current renderer copies one section per page. Grouping will change page
  composition only, retaining native plots, tables, precision and selector inputs.
- Scope: optional strict `report_groups` config, ordered group pages and tab
  navigation, internal output links, selector/deep-link preservation, tests,
  report-only replay into a fresh output directory, ZIP and browser review.
- Use the already established candidate environment and report-only tmux after
  refreshing access, read visits and output-root lock. Never alter controllers.

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| GROUP-01 | Renderer | Strict grouping with every visible section assigned exactly once | SUCCESS | feature_implementation | 1 | primary | 106 unique anchors in ten groups; schema, docs and negative tests | | No omitted or duplicate assignment |
| GROUP-02 | UI | Ordered tabs and in-group navigation with lazy group loading | SUCCESS | feature_implementation | 2 | primary | Chrome local-file checks of all ten tabs, fresh-session deep link and Back state | | Group plots and tables load independently |
| GROUP-03 | Tests | Config errors, native data and navigation regression | SUCCESS | contract_test | 3 | primary | 40 grouping/config, 28 existing-report Python and 20 JS tests; npm build rc=0 | | Includes exact table model equality in grouped fixture |
| GROUP-04 | Example | 48-AU existing-FSx render and documented draft02 content/data comparison | SUCCESS | contract_test | 4 | primary | Draft04 render rc=0; all table values identical; comparison and jitter investigation below | | Draft generation/comparison complete, not full scientific acceptance |
| GROUP-05 | Delivery | Offline browser check, ZIP and review handoff | SUCCESS | contract_test | 5 | primary | 52 MiB ZIP downloaded, checksum matched; index and stage screenshots reviewed | | Review draft ready; original full-plan gates remain open |

This amendment's completion is separate from the full original plan's open
scientific parity, precision, cross-browser and performance acceptance gates.

Independent review (Astra xhigh) identified two issues before handoff:
within-tab links must carry selector state and restore it on history changes;
the bundle comparison must flag changed scientific exports for investigation,
even when table/plot payloads match. Corrected both and added navigation
regressions. Also scoped group scroll offsets to grouped reports only.
The corrected draft04 supersedes draft03 for review; both are preserved.

## Final grouped draft evidence, 2026-09-06 07:56 UTC

- Renderer commit `ff127e1f00c8f84a317a17d99843ba4d89348fde` on the isolated
  feature branch only. Final wheel SHA-256
  `cb236b56c3e513636f7a7161b15629800f152a421a5b46b04539ea57612a57e1`.
- `report-draft04-grouped/render-receipt.json`: MultiQC rc=0,
  160.2842 seconds, peak child RSS 2,275,032 KiB; 4,263 source files and
  original report/config hashes unchanged, zero scientific workflows launched.
- Eleven HTML pages: Overview plus ten tabs. Section counts in order:
  Raw Reads 15, Alignment 13, Coverage 6, SNVs & Indels 7, SVs & CNVs 16,
  Specialized Calls 5, Identity & Contamination 25, QC Metrics 3,
  Validation 4, Provenance & Runtime 12. Total 106, each assigned once.
- 101 plot definitions, 56 complete table models, 24,305 table rows,
  121,999 numeric table cells, 17,303 selector records, 146 scientific exports.
- Every table model, stored numeric cell and selector record equals draft02.
  99 plot definitions match exactly. The two differences are categorical-X
  jitter in Peddy (48 points) and Somalier (96 points). The bounded check in
  `20260906T073317Z_check_grouped_jitter.py` verified identical sample names,
  measured Y values, sex categories and all other plot properties, plus the
  corresponding exported TSV columns. Only X jitter changes within +/-0.05
  of the same categorical coordinate. No report or source was changed by this
  investigation.
- The strict byte-comparison diagnostic returns rc=1: six exports
  differ bytewise (`llms-full.txt`, `multiqc.log`, `multiqc.parquet`,
  `multiqc_data.json`, and the two sex-check plot TSVs). JSON top-level
  differences are command, creation date, comment, title, output directory and
  those same two jittered plot dumps; all other fields match. Following the
  user's clarification, byte identity is not the scientific acceptance gate.
  Hashes remain source-integrity and transfer checks. Acceptance concerns
  presented measurements, identities, units, statuses and meaningful precision;
  timestamps, file layout and within-category jitter are not scientific changes.
  The original plan's exhaustive rendered-value/export acceptance remains open;
  in particular, Parquet semantic parity has not been independently audited.
- Chrome 152 local-file navigation reached all ten tabs with their exact
  expected plot counts (13/13/6/7/16/5/23/3/4/11), no visible resource errors
  and zero HTTP(S) resource requests during these checks. These are functional
  spot checks, not formal performance or multi-browser acceptance.
- Shared GIAB deep link reopened in a fresh browser context with SR selected.
  Same-document Back restored LR and then SR consistently with URL state.
  Within-tab scrolling reached the intended output. Report context links open
  the collapsed context panel. All-mode GIAB spot check: 50 visible rows,
  351 integer cells and zero rounding mismatches. FDR 0.0006842177795077984
  displays as 0.000684218.
- Browser review screenshots: `output/playwright/ilmn14-grouped-draft04-index.png`,
  `ilmn14-grouped-draft04-validation.png`, `ilmn14-grouped-draft04-giab.png`.
- Latest focused checks: 51 Python tests plus 10 config/comparison tests;
  21 JavaScript tests; npm build rc=0. One test invocation overlapped a clean
  frontend rebuild and correctly failed on missing temporary CSS; serialized
  rerun after build passed. Initial candidate install without build isolation
  lacked setuptools; using the declared isolated build dependencies succeeded.
  Neither issue modified production environments or scientific results.
- Fresh-context reviewer confirmed both findings corrected, with no further
  actionable regression in the reviewed grouping changes. Review did not claim
  independent verification of real scientific data.
- ZIP SHA-256: `3d5ac6c4a049c672f40f0db788ee3a422bda2ca0e39bb274c701e620f6c8ca8e`.
  FSx and Mac match; extraction and all bundle file hashes verified.
- Local ZIP: `output/ILMN-14_48AU_grouped_draft04.zip` (about 52 MiB).
  Entry: `output/ILMN-14_48AU_grouped_draft04/report-draft04-grouped/index.html`.
  Comparison receipt: `output/ILMN-14_48AU_grouped_draft04/comparison.json`.
- Private S3 relay retained at
  `s3://lsmc-ssf-sequencing-data/_codex_report_previews/ilmn14-pagination-20260906t064750z/dyec-headnode-transfer/pclu-19074/20260906T074926Z-f978cd2258cb/ILMN-14_48AU_grouped_draft04.zip`.
  No public publication or S3 deletion. No new DRA was required.
- FSx output-root lock released. Interactive SSM and the named idle report-only
  tmux shell remain open. Historical controllers and all previous drafts are
  preserved. No merge, tag or production pin change.

All five amendment rows terminal: yes, 5 SUCCESS. Grouped review-draft objective
complete: yes. Full original implementation objective complete: no. In
particular, the approximately 3.6 MiB index still exceeds the 2 MB target;
whole-report AI metadata deduplication, full numeric/plot acceptance,
Inflection integration, 192-AU scaling and cross-browser gates remain open.

## Header layout amendment, 2026-09-06 08:04 UTC

User requests report title above stage tabs, logo at the upper right on the
index and all section pages, and the active section title above the Report
index sidebar link. Baseline: clean candidate branch at `763515a38`, draft04
preserved. Only template layout and compiled presentation CSS will change.
Explicit user direction: skip tests and regenerate from the existing 48-AU
FSx inputs. No scientific workflows, comparisons, browser tests or release.

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| HEADER-01 | Template | Global title/logo and section-first sidebar | SUCCESS | feature_implementation | user request | primary | Shared paginated masthead, header guard and CSS; asset build complete | | Tests explicitly skipped by user direction |
| HEADER-02 | Example | Regenerate 48-AU report and provide review files | IN_PROGRESS | feature_implementation | user request | primary | Existing FSx inputs, fresh draft05 output | | |

Candidate renderer: `fd1087f3571db53e6fa54c90b59cc5fa5c104b09`.
Report-only environment wheel SHA-256:
`459154c02bd1eb47d8495e0d9e9b677521ba0649b030fe005e53947a5d0960b5`.
Reused the existing one-window/one-pane interactive report tmux on pclu-19074.
Recorded source read visit and acquired the candidate output-root write lock.
Other cluster jobs belong to the separate segdup-tuning analysis and were not
modified. This request submits no scientific workflow work.
