# Six-Manifest Native MultiQC Lane Ledger

## Scope

Replace the LSMC `snakemake_samples` three-manifest contract with the exact
DayOA 13 six-manifest model. Preserve every entity grain and the ordered
many-to-many analysis-unit input topology. Do not create a compatibility
projection that makes a physical library look like an analysis unit.

This lane is local-only. A0 owns integration, push, release, and tagging.

## Gate 0

| Item | Evidence | Status |
|---|---|---|
| Worktree | `/Users/jmajor/projects/lsmc/MultiQC` | SUCCESS |
| Branch | `codex/six-manifest-native-multiqc` | SUCCESS |
| Base annotated tag object | `1.36.dev0-lsmc.9`, object `a56893d20efc0ac91c54f542a9a94c9ad7a0e260` | SUCCESS |
| Base peeled release commit | `421bab7a9b02d847da280e8d287f169adef7ce56` | SUCCESS |
| Primary and prior worktrees | Preserved; prior `.playwright-cli/` remains untouched in its owning worktree | SUCCESS |
| Service boundary | No Dayhoff, Ursa, Bloom, TapDB, Dewey, network identity, or service mutation | SUCCESS |

## Execution

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| MQ6-001 | Parse five entity manifests plus the analysis-unit input join | SUCCESS | Native parsers and exact search patterns claim all six files. |
| MQ6-002 | Validate exact keys, FKs, `MODALITY`, `LAYOUT`, roles, and ordinals | SUCCESS | Positive and negative parser tests; 94% parser coverage. |
| MQ6-003 | Render source-grain tables plus resolved ordered analysis-unit selections | SUCCESS | Strict synthetic render completed with six native sections. |
| MQ6-004 | Preserve exact identifiers in downloads and selector-visible row keys | SUCCESS | Six native downloads and report snapshot retain exact IDs and declared arrays. |
| MQ6-005 | Reject old three-file library-as-analysis-unit shape | SUCCESS | Focused regression test rejects `ANALYSIS_UNIT_UID`-keyed `libraries.tsv`. |
| MQ6-006 | Run focused/full tests, strict render, and browser-console QA | SUCCESS | `test_result_evidence/20260719T025551Z_six_manifest_native_multiqc.md`; 42 focused tests passed, 0 browser errors/warnings. External-fixture comparison: candidate 382 passed/53 inherited failures; exact `.9` baseline 340 passed/the same 53 failures. |
| MQ6-007 | Commit local candidate for A0 integration | SUCCESS | This ledger and the native module candidate are committed together on `codex/six-manifest-native-multiqc`; A0 owns push, tag, and release. |

## Decisions

- Candidate release is the next unclaimed tag after `.9`, normally
  `1.36.dev0-lsmc.10`; this lane does not tag or push it.
- DayOA 13 passes the exact six TSVs to the native module. It does not stage
  report-local custom tables as a substitute and does not synthesize
  `ANALYSIS_UNIT_UID` in `libraries.tsv`.
- Every native table retains its source key. Resolved analysis-unit selection
  columns are derived only from the explicit join and preserve declared input
  ordinal order.
