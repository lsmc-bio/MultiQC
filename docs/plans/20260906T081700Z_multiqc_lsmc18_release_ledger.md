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
| REL-01 | Source | Commit/push release documentation and PR | IN_PROGRESS | feature_implementation | user release request | primary | Detailed notes and this ledger | | |
| REL-02 | Merge | Observe checks and merge PR normally | OPEN | feature_implementation | repository policy | primary | Pending | | |
| REL-03 | Tag | Annotated immutable 1.36.dev0-lsmc.18 on clean merged commit | OPEN | feature_implementation | user version selection | primary | Pending | | |
| REL-04 | GitHub | Publish detailed tagged release and return URL | OPEN | feature_implementation | user release request | primary | Pending | | |

Full original development-plan acceptance remains separate from this approved
source-release objective. Release notes:
`docs/plans/20260906T081700Z_multiqc_lsmc18_release_notes.md`.
