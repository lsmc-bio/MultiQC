# vcf-sv-stats explicit no-content-hash ingestion

Created: 2026-09-12 22:16:42 UTC.

## Gate 0

- Scope: isolated MultiQC dependency integration for DayOA's requested removal of workflow file-content hashing.
- Source: annotated tag `1.36.dev0-lsmc.19`, peeled commit `bec19c966`.
- Worktree: `/Users/jmajor/projects/lsmc/MultiQC-no-content-hash-20260912`.
- Branch: `codex/multiqc-no-content-hash-20260912`.
- Original checkout is untouched. Its baseline contains modified `AGENTS.md`, untracked `.coverage` and `.playwright-cli/`.
- Inventory: `multiqc/modules/vcf_sv_stats/parser.py` hashes the summary payload and each report; `vcf_sv_stats.py` treats matching summary hashes as duplicate equivalence.
- Producer source contract: `/Users/jmajor/projects/lsmc/sv-vcf-stats-no-content-hash-20260912/src/vcf_sv_stats/schemas/summary-1.1.0.json` and `engine.py`.
- Tests, lint, builds, runtime commands, commits, releases and deployment are excluded by the current assignment. Source review only.

## Ledger

| ID | Requirement | Status | Owner | Evidence / terminal note |
|---|---|---|---|---|
| MQ-001 | Accept explicit schema 1.1.0, require null digests and attempt identity | SUCCESS | multiqc_nohash | Parser requires hash_policy=not_performed, null input/payload SHA, UUID v4 attempt, matching callset and ordinal report IDs; statistical validation is unchanged. Source review only. |
| MQ-002 | Avoid payload/report hashing in this mode and reject repeated unverified IDs | SUCCESS | multiqc_nohash | Both digest calls are skipped in schema 1.1.0. Consumer explicitly rejects repeated no-hash report IDs before legacy duplicate comparison. |
| MQ-003 | Expose measurement policy honestly in exported/report data | SUCCESS | multiqc_nohash | Export has hash_policy and attempt_id; provenance table states Not performed. Null values do not establish byte identity. |
| MQ-004 | Record exact DayOA environment integration and release proposal | SUCCESS | multiqc_nohash | Integration instructions below; project version is 1.36.0. |
| MQ-005 | Remove DayOA six-manifest normalized-row provenance hash | SUCCESS | multiqc_nohash | snakemake_samples no longer serializes/hashes parsed rows for provenance; normalized_rows_sha256 is null and hash_policy is not_performed. Existing manifest reconciliation and lineage checks remain. Existing assertion updated, not executed. |

Runtime acceptance and release remain parent-owned gates. This source work does not establish successful workflow execution.

## Release and DayOA integration

- Proposed immutable annotated numeric fork release: `1.36.0`, explicitly based on `1.36.dev0-lsmc.19`. This is the LSMC fork's release identity, not an assertion about an upstream MultiQC release.
- `pyproject.toml` owns package version; `multiqc/config.py` obtains it from installed package metadata. No other owned version constant was found.
- Parent must commit the intended changes, push the working branch and annotated tag. No commit, push or tag was performed by this agent.
- New DayOA environment YAMLs must replace the existing MultiQC tag URL with `multiqc @ https://github.com/lsmc-bio/MultiQC/archive/refs/tags/1.36.0.zip` only after that tag exists.
- Preserve every existing versioned YAML. Copy the relevant current contracts to incremented filenames: current rules reference `multiqc_v0.10.yaml` (slim consensus and final WGS branch), `multiqc_v0.11.yaml` (Inflection packaging), and `multiqc_v0.12.yaml` (final WGS reporting). Preserve their individual dependency sets; do not collapse them into one inferred environment.
- Point each corresponding DayOA rule at its explicit new environment YAML. Keep the current Plotly/Kaleido pair and other rendering dependencies unchanged.
- DayOA's vcf-sv-stats adapter must require producer `1.1.2`, request `stats --no-content-hash`, and require summary `1.1.0`, `hash_policy=not_performed` and null hashes. The MultiQC parser accepts that explicit producer schema without a separate module configuration toggle.
- The external legacy schema 1.0.0 remains an explicit separate contract with its existing digest behavior. DayOA must not feed legacy schema 1.0.0 summaries to this rule when enforcing its no-hash policy.

## Source review and final state

- Read the producer's schema and report ID construction and compared parser requirements directly. No tool execution was used as a test.
- Read the complete changed source diff. Existing scientific count, histogram, diagnostic, breakend, sample mapping and metric-contract checks remain on both supported schema paths.
- Reviewed `rg -n 'sha256|hashlib|rfc8785' multiqc/modules`: runtime module hash computation remains only in the explicit vcf-sv-stats schema 1.0.0 path. Test fixture hashes remain historical fixtures.
- No tests, lint, build, MultiQC report generation, AWS access or runtime deployment were run.
- All five implementation rows are terminal SUCCESS for the source-only assignment. Release, installed dependency identity and live DayOA acceptance are not complete and remain parent-owned.
