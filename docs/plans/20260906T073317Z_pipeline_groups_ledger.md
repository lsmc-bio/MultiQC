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
| GROUP-02 | UI | Ordered tabs and in-group navigation with lazy group loading | IN_PROGRESS | feature_implementation | 2 | primary | Native independent pages; browser check pending | | |
| GROUP-03 | Tests | Config errors, native data and navigation regression | SUCCESS | contract_test | 3 | primary | 40 grouping/config, 28 existing-report Python and 20 JS tests; npm build rc=0 | | Includes exact table model equality in grouped fixture |
| GROUP-04 | Example | 48-AU existing-FSx render and draft02 content/data comparison | IN_PROGRESS | contract_test | 4 | primary | Read visits, empty queue, single idle report tmux and acquired output lock verified | | |
| GROUP-05 | Delivery | Offline browser check, ZIP and review handoff | OPEN | contract_test | 5 | primary | Pending | | |

This amendment's completion is separate from the full original plan's open
scientific parity, precision, cross-browser and performance acceptance gates.

Independent review (Astra xhigh) identified two issues before handoff:
within-tab links must carry selector state and restore it on history changes;
the bundle comparison exit code must reject changed scientific exports, even
when table/plot payloads match. Corrected both and added navigation regressions.
Also scoped group scroll offsets to grouped reports only. Draft03 rendering
continues on its frozen candidate; a corrected fresh draft will follow.
