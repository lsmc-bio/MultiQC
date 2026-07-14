# HG003 1x HIOMRS Whole-Tree MultiQC Execution Ledger

Date: 2026-07-13

## Objective

Preserve the existing DayOA MultiQC report, make the local native MultiQC modules compatible with the complete HG003 1x HIOMRS result tree, publish a strict new report named `DAY_fin_new_multiqc.html`, and leave a reproducible unpublished-build adoption guide.

## Controlling Paths

- MultiQC repository: `/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712`
- Branch: `codex/snakemake-samples-hybrid-qc`
- Baseline commit: `2fcad4e380de1d620844837c8913b935ef957a6f`
- Cluster: `sent-hg003-5x-0712`
- Analysis root: `/fsx/analysis_results/sent-hg003-5x-0712/hg003-1x-ks-1030-20260713T092619Z/daylily-omics-analysis/results/day/hg38`
- Existing report: `reports/DAY_final_multiqc.html`
- New report: `reports/DAY_fin_new_multiqc.html`
- Adoption guide: `reports/DAY_fin_new_multiqc_adoption.md`

## Gate 0 Baseline

- Repository state at start: branch is 5 commits ahead of `origin/codex/ultima-alignstats-native`; feature work is intentionally uncommitted.
- Existing modified surfaces: `multiqc/core/ai.py`, AlignStats, Ultima, search patterns, and `pyproject.toml`.
- Existing untracked surfaces: the prior feature ledger and the `snakemake_samples` and `snakemake_benchmarks` modules.
- User contract: do not commit, push, tag, or update DayOA environment pins.
- Live baseline from the completed DayOA controller: workflow returned success and produced `reports/DAY_final_multiqc.html` with its data directory. The old report must remain byte-identical.
- No report input may be silently overwritten or reconciled by path precedence. Repeated inputs require normalized equality or a hard failure naming every conflicting path.

## Execution Ledger

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| INV-001 | Live inventory | Record the required read visit, verify lock state, inventory every result-tree file, and capture old report hashes and module data | SUCCESS | feature_implementation | Gate 0 | inventory-agent | Visit recorded; lock `unlocked`; 1,317 files, 188 dirs, 6,294,659,041 bytes; controller 12/12 success; old 98-file aggregate hash `b2a4db7b...` |  | Baseline frozen under `/home/ubuntu/multiqc-hg003-1x-inventory-20260713T173512Z/` |
| INV-002 | Candidate accounting | Classify every file and produce the final input inventory with recognition key, disposition, provenance, and candidate hashes | SUCCESS | feature_implementation | Gate 5 | inventory-agent | Inventory SHA `3afe2e0a...`; 753 hashed candidates; 101 identical duplicate groups; 196 staged rows across 32 modules |  | Every tree file has one disposition; no Hybrid or Ultima inputs found |
| MQC-001 | Samples | Parse raw and staged samples and units schemas and require exact normalized equality when both exist | SUCCESS | feature_implementation | Gate 4 | multiqc-agent | Staged-only and raw-plus-staged module tests pass; live raw/derived one-row manifests normalize exactly |  | Native Samples and Libraries support both DayOA representations |
| MQC-002 | Reconciliation | Deduplicate identical repeated manifests and gender files and reject conflicting content with all paths | SUCCESS | legitimate_safety_handling | Gate 4 | multiqc-agent | Duplicate and negative-conflict tests pass; provenance raw data records all paths |  | No silent path precedence or last-write behavior |
| MQC-003 | AlignStats | Reconcile combo and native records only when overlapping normalized metrics agree | SUCCESS | legitimate_safety_handling | Gate 4 | multiqc-agent | Identical combo, `alignstats_gs`, native merge, and conflict-path tests pass |  | Overlap equality uses exact numeric normalization |
| MQC-004 | Ultima | Remove last-write-wins duplicate behavior and enforce identical-content deduplication or failure | SUCCESS | removable_compatibility_debt | Gate 4 | multiqc-agent | Identical-row and conflicting-row module tests pass |  | Live run has no Ultima inputs, but the native contract is proven locally |
| MQC-005 | Benchmarks | Require sample, deduplicate repeated combined inputs, and report rule-level walltime, vCPU time, and cost tables and boxplots | SUCCESS | feature_implementation | Gate 4 | multiqc-agent | Valid 24-column raw header, required sample, duplicate/conflict, shifted-row failure, aggregation, and strict-render tests pass |  | Four distributions plus summary table are emitted |
| MQC-006 | Hybrid QC | Parse only a valid defined custom input; never synthesize missing measurements or thresholds | SUCCESS | legitimate_safety_handling | Gate 4 | multiqc-agent | Exact ordered 22-column schema and nine-check evaluation tests pass |  | Live section is legitimately absent because no producer input exists |
| MQC-007 | Search routing | Prefer native inputs over generic custom content while retaining existing DayOA stock and custom sections | SUCCESS | config_or_startup_contract | Gate 4 | multiqc-agent | YAML precedence assertions and staged native-vs-custom search test pass |  | Native handlers capture their inputs before generic custom content |
| TST-001 | Focused tests | Pass parser, module, duplicate, conflict, schema, and strict synthetic render tests | SUCCESS | contract_test | Gate 5 | multiqc-agent | `pytest` -> 52 passed in 3.01s; strict four-module render at `/private/tmp/multiqc-hg003-local-final-strict/local_final_strict.html` |  | Required exported raw-data keys verified in `multiqc_data.json` |
| TST-002 | Quality | Pass Ruff, MyPy, code checks, compile/schema checks, and relevant integration tests | SUCCESS | contract_test | Gate 5 | orchestrator | Ruff pass; MyPy 15 final source files pass; `code_checks.py` pass; YAML and shell syntax pass; `npm run build` pass; `git diff --check` pass |  | Full `tests/test_modules_run.py` requires the absent test-data submodule; focused modules, strict live rendering, and browser smoke testing provide the relevant gate |
| AMD-001 | Transport amendment | Use an analysis-scoped immutable S3 key for the binary wheel because DYEC exposes no supported binary-copy command | SUCCESS | plan_amendment | Gate 5 | orchestrator | `dyec headnode --help` exposes no binary transfer; `write_remote_text` is explicitly small-text only; proven headnode-readable prefix is `s3://lsmc-ssf-sequencing-data/derived/dayoa_input_staging/20260713T125855Z_bjuice_prevalidation_hiomrs_1038/` | The planned DYEC binary helper does not exist | Wheel will use `multiqc_unpublished/hg003-1x-ks-1030-20260713T092619Z/<dirty-diff-sha256>/`; no shared runtime-fixes key and no deletion |
| AMD-002 | Benchmark input amendment | Render from a validated scratch copy of the final raw benchmark summary, excluding all original benchmark snapshots from the scan | SUCCESS | plan_amendment | Gate 5 | orchestrator | Raw hash `508a5ff...`, 148 rows at 16:18:03Z; strict row validation found 130 sample/rule-scoped rows and 18 unscoped path rows with shifted columns; canonical SHA `5b08334b...`; rejection ledger SHA `07cef5a1...` | Whole-tree benchmark snapshots are intentionally not equal, and 18 source rows omit the declared sample/rule shape while shifting `h:m:s` into numeric `s` | Preserve all 130 valid final rows, reject all 18 malformed rows with line-level hashes, keep the module conflict-hard, and explicitly exclude the three original snapshots |
| PKG-001 | Provenance | Build an unpublished wheel and record branch, base commit, dirty diff hash, wheel name, and SHA-256 | SUCCESS | feature_implementation | Gate 5 | render-agent | Branch `codex/snakemake-samples-hybrid-qc`; base `2fcad4e380de1d620844837c8913b935ef957a6f`; source fingerprint `6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517`; wheel `multiqc-1.36.dev0-py3-none-any.whl` SHA `df4f2eaba4d5bef32edd5f7f5b15277d6ed9addc864c543e7c1c23dfc4b18c82` |  | Immutable wheel stored under the analysis-scoped unpublished S3 prefix; no release operation performed |
| LIVE-001 | Scratch render | Install the wheel in an isolated headnode environment and complete a strict whole-tree scratch render | SUCCESS | contract_test | Gate 5 | orchestrator | Dedicated environment `/home/ubuntu/.local/share/multiqc-hg003-1x-conda-eab70e9a`; final strict render exit `0`; log `/home/ubuntu/multiqc-hg003-1x-render-20260713/live_strict_render-6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517.log`; generated config SHA `94177f5271c0adbdcde6257f39b71587a97859c6423c5b7aac0045cd23e2fa2c` | The released DayOA config retained custom search keys for inputs now owned by native modules; the initial isolated render also exposed a disabled-AI browser path that treated Python `None` as the provider string `"None"` | The exact final wheel uses a narrow render overlay for migrated custom keys and a compiled browser fix; strict rendering is clean |
| LIVE-002 | Report validation | Validate expected sections, exported data, source accounting, duplicate absence, and browser rendering | SUCCESS | contract_test | Gate 5 | render-agent | JSON/HTML assertions: Samples 1, Libraries 1, gender check 1 PASS, AlignStats 2, Somalier 2, benchmark rows 130 across 127 rules, Ganon 2, Mosdepth 46, Picard 6 subtools; official Playwright snapshot `.playwright-cli/page-2026-07-13T20-13-58-488Z.yml` and console `.playwright-cli/console-2026-07-13T20-13-56-877Z.log` |  | No console errors or warnings; Hybrid section absent with producer-unavailable provenance; required navigation links present |
| LIVE-003 | Guarded publication | Acquire the analysis lock and publish the new HTML, data directory, inventory, and adoption guide through a guard | SUCCESS | feature_implementation | Gate 5 | orchestrator | Required write visits recorded; agent-owned write lock acquired and released without takeover; guarded publication and final export exit `0`; HTML SHA `51a9694608b714de3b7c2638c9b899d83035fc1920c95bc1d8ab9a32eb07a763`; data JSON SHA `8e3488708df6dd4070e7136058a877eb27f36173fafcd0976bea7d7219270a15` |  | Published under `reports/DAY_fin_new_multiqc*` and copied to `/Users/jmajor/projects/lsmc/fin_multiqc/` |
| PRES-001 | Preservation | Prove the existing report and data files are unchanged before and after publication | SUCCESS | legitimate_safety_handling | Gate 5 | orchestrator | Old HTML SHA remains `19ac94708a78dc3386e01197497fdb5e67a4ca98b75033f5e64dfae4b1f9894d`; old data JSON SHA remains `da8d23f38f0bba5e9f8e8997a191ea7155a107483cb55c8ef8e2028b3a2a848f`; old 98-file aggregate remains `b2a4db7bae046e1832b00a48432b05813726da76ab585fdb85710c6946fb7d89` |  | Historical report and data directory were not modified |
| DOC-001 | Handoff | Write repository and report-side adoption instructions for the exact unpublished build | SUCCESS | feature_implementation | Gate 5 | render-agent | Repository guide `docs/plans/20260713T161440Z_hg003_1x_hiomrs_multiqc_adoption.md`; report-side SHA `c85208367dd349bead5c1aa7f580028441f3d6633b7b5e033d8cdb63fcfb2363` |  | Documents exact source, wheel, environment, config, exclusions, command, expected outputs, and unpublished-release boundary |
| AMD-003 | Browser amendment | Keep disabled AI from dereferencing a provider while retaining environment-derived default-model behavior when AI is enabled | SUCCESS | plan_amendment | Gate 5 | orchestrator | Source and compiled assets rebuilt with Vite; disabled AI resolves provider to `none`; enabled AI retains provider/config and environment-derived model routing; official report browser smoke test has no errors or warnings | Python `None` was serialized into the page as the literal provider string `"None"`, so disabled AI attempted to resolve an undefined provider | No default model is hard-coded; the environment remains authoritative when AI is enabled |
| ACC-001 | Final acceptance | Terminalize every row and distinguish terminal ledger state from objective completion | SUCCESS | contract_test | Gate 5 | orchestrator | All ledger rows terminal `SUCCESS`; final report, data, inventory, benchmark rejection ledger, adoption guide, local copy, preservation hashes, strict exit, and browser evidence verified |  | Objective complete; Hybrid is explicitly unavailable because the required producer file does not exist |

## Execution Constraints

- Record `dyec analysis visit` before inspecting the analysis root.
- Live writes require owned analysis-root lock and `dyec analysis guard`.
- Never take over another lock owner without the token flow and explicit double approval.
- Exclude prior MultiQC HTML and data directories from parsing, but retain `reports/multiqc_inputs/**`.
- Catalog primary BAM, CRAM, VCF, and similar payloads without reading them as MultiQC inputs.
- Missing Hybrid Seq Batch QC input is an explicit unavailable producer state, not permission to fabricate a section.
- The old report is historical evidence and must never be overwritten.
- No commit, push, tag, release, or DayOA environment pin change is authorized.

## Final Terminal-State Report

- Every execution-ledger row is terminal `SUCCESS`; the objective is complete.
- The strict final report is published at `reports/DAY_fin_new_multiqc.html` with HTML SHA-256 `51a9694608b714de3b7c2638c9b899d83035fc1920c95bc1d8ab9a32eb07a763` and copied with its complete artifact set to `/Users/jmajor/projects/lsmc/fin_multiqc/`.
- The report contains native Samples, Libraries, reported-versus-observed gender, AlignStats, Somalier, Snakemake Benchmarks with walltime/vCPU/cost distributions, and all recognized stock/custom sections from the live configuration.
- Hybrid Seq Batch QC is explicitly unavailable: no valid `hybrid_seq_batch_qc.tsv` producer output exists in the complete result tree, and no values were fabricated.
- The old report and data-directory hashes are unchanged. The final strict live render exits zero, browser smoke testing has no console errors or warnings, and no duplicate logical samples remain.
- The source is a proven unpublished dirty build. No commit, push, tag, release, or DayOA pin update was performed.
