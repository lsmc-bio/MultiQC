# MultiQC lsmc.18 release ledger

User approved draft05 and requested commit/push, a new tag and a GitHub release
with detailed release notes. User explicitly selected the existing fork version
sequence `1.36.dev0-lsmc.18`, overriding the ship-release skill's numeric-only
format. This authorizes MultiQC source release, not DayOA adoption, PyPI
publication, report-data publication or cluster changes.

## Gate 0

- Repo: `/Users/jmajor/projects/lsmc/MultiQC-paginated-20260906`.
- Branch: `codex/paginated-multiqc-20260906`, clean at `b21e4243e`.
- Origin: `https://github.com/lsmc-bio/MultiQC.git`, default branch `main`.
- Fresh remote maximum fork tag: `1.36.dev0-lsmc.17` at `7cb01ef4d`.
- Remote main: `c6799becd`; release branch retains the earlier lsmc.16/.17
  changes that were tagged but not yet ancestors of main.
- No pre-existing PR for the release branch. Organization rules require a PR,
  prohibit non-fast-forward/deletion and require zero ordinary approvals.
- No unrelated working-tree changes. Existing reports and historical clones
  are outside release mutation scope. Git tag signing is not configured.
- No new local test suite. Existing focused/browser/generation evidence and
  open limitations are explicit in the release notes. GitHub checks will be
  observed without manual dispatch or admin bypass.
- Repository release workflows guard actual upstream PyPI and Docker
  publication by repository identity; no twup or package upload is requested.

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause | Terminal note |
|---|---|---|---|---|---|---|---|---|---|
| REL-01 | Source | Commit/push release documentation and PR | SUCCESS | feature_implementation | user release request | primary | PR https://github.com/lsmc-bio/MultiQC/pull/13 | | Release branch and notes pushed |
| REL-02 | Merge | Observe checks and merge PR normally | ATTEMPTING_BUGFIX | feature_implementation | repository policy | primary | Initial CodeQL gate failed on client-side regex HTML stripping | Incomplete multi-character sanitization in clipboard unit formatting | |
| REL-03 | Tag | Annotated immutable 1.36.dev0-lsmc.18 on clean merged commit | OPEN | feature_implementation | user version selection | primary | Pending | | |
| REL-04 | GitHub | Publish detailed tagged release and return URL | OPEN | feature_implementation | user release request | primary | Pending | | |

Full original development-plan acceptance remains separate from this approved
source-release objective. Release notes:
`docs/plans/20260906T081700Z_multiqc_lsmc18_release_notes.md`.

Initial CodeQL analysis jobs completed successfully, but the security gate
reported one high-severity alert at `src/js/paginated.js:29`, incomplete
multi-character sanitization in the unit suffix formatter. Replaced the regex
with parser-based plain-text extraction in the generated clipboard row model;
the client now consumes that text without HTML stripping. Raw numeric values,
precise scientific exports and native table HTML are unchanged. Added a focused
regression case; no local tests were executed. Rebuilt frontend assets and
will require the automatic GitHub check to clear without suppression or bypass.
