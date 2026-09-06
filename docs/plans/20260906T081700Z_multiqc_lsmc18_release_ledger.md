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
| REL-02 | Merge | Observe checks and merge PR normally | SUCCESS | feature_implementation | repository policy | primary | All three checks passed on 37bc1f84c; PR 13 merged 2026-09-06T08:23:30Z | Initial regex stripping alert corrected | Normal merge within lsmc-bio only, no bypass |
| REL-03 | Tag | Annotated immutable 1.36.dev0-lsmc.18 on clean merged commit | SUCCESS | feature_implementation | user version selection | primary | Local and remote peeled commit 400f3de84aa4470f8c36bbd76c037d9f9e9176e1 | | Annotated tag verified and pushed |
| REL-04 | GitHub | Publish detailed tagged release and return URL | SUCCESS | feature_implementation | user release request | primary | Published 2026-09-06T08:23:51Z; URL below | | Published release, not draft; no report data attached |

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
required the automatic GitHub check to clear without suppression or bypass.

## Terminal release receipt

- All four release rows are terminal SUCCESS. Approved source-release objective
  complete; original broader development acceptance and DayOA adoption remain
  separate and incomplete as documented in the release notes.
- PR: https://github.com/lsmc-bio/MultiQC/pull/13.
- Both PR base and head repositories verified as `lsmc-bio/MultiQC`. No request
  or mutation was made to upstream `MultiQC/MultiQC`.
- Corrective source commit: `37bc1f84c5b12e5e4f31f099dd691b9a5a45512e`.
- GitHub run `34021630092`: JavaScript/TypeScript analysis SUCCESS (81s), Python
  analysis SUCCESS (52s); CodeQL security gate `101455265523` SUCCESS (3s).
- Clean merged release commit: `400f3de84aa4470f8c36bbd76c037d9f9e9176e1`.
  Local main was fast-forwarded to this exact commit before tagging.
- Tag `1.36.dev0-lsmc.18`, annotated object
  `5d42b6d8f9aabb728d7c10009798016d31db3136`. Remote tag and peeled commit match.
- Release: https://github.com/lsmc-bio/MultiQC/releases/tag/1.36.dev0-lsmc.18.
  Published, not draft, not prerelease, designated latest. Detailed notes
  supplied from the committed release-notes file. No customer report assets.
- Final receipt is recorded after publication on a documentation-only audit
  branch, `codex/lsmc18-release-receipt-20260906`; it does not move the tag or
  change release code. No PyPI upload, production pin update or cluster action.
