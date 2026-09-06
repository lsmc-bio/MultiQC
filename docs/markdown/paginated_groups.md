# Pipeline-stage report groups

Use `multiqc --template lsmc-paginated --config report.yaml` to render ordered
groups as tabs. Each tab is an independent HTML page with only its own detailed
data. Native plots initialize as they become visible. The overview indexes all
groups and all individual outputs. The extracted folder opens without a server.

```yaml
report_groups:
  - id: reads
    title: Raw Reads
    description: Read quality and input composition.
    modules: [toolname]
  - id: qc
    title: QC Metrics
    sections: [general_stats, another_exact_section_anchor]
```

`modules` selects all visible sections of an exact module anchor. `sections`
selects exact section anchors, allowing one tool to be split across tabs. These
are output anchors, not fuzzy display-name matches or glob patterns. Both keys
may be supplied in a group, but their selections must not overlap. Group list
order determines tab order; native order is retained within groups. Titles and
descriptions are escaped text. IDs must be unique lowercase slugs.

Every visible section must be assigned exactly once. Unknown selectors, repeated
assignments, empty groups, unknown keys and unassigned outputs are errors. The
error lists unassigned anchors to aid configuration. `general_stats` is an
explicit section selector when General Statistics is enabled. Omit
`report_groups` to request the existing one-page-per-section presentation.

The manifest records group configuration, original section membership, plot IDs,
table counts and files. Grouping changes require report rendering; the
presentation-only refresh utility does not regroup scientific pages. Display
precision and styling remain independently configurable.

Ordinary links implement tabs, preserving offline operation and browser history.
Selector state and a deep-linked output anchor coexist in the URL fragment; S3
signature query strings are not modified. Navigating does not load other groups.
Native browser caches may retain a prior document; no cross-group application
data store is introduced. Full multi-browser memory acceptance remains pending.
