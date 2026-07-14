# Snakemake Samples and Hybrid Seq Batch QC Control Ledger

Controlling request: integrate all current upstream MultiQC release-line changes into the LSMC native AlignStats line, then add a native handler for Snakemake `samples.tsv`, `units.tsv`, reported versus observed gender checks, and per-library Hybrid Seq Batch QC.

Ledger path: `docs/plans/20260712T223037Z_snakemake_samples_hybrid_qc_ledger.md`

## Gate 0: Inventory Freeze

- Checkout: `/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712`
- Branch: `codex/snakemake-samples-hybrid-qc`, created from `origin/codex/ultima-alignstats-native` at `1955aa49` (`1.36.dev0-lsmc.6`).
- Upstream integration: merged `upstream/main` at `14f07146` in merge commit `2fcad4e3`. `git rev-list --left-right --count HEAD...upstream/main` returned `7 0`; the branch contains every current upstream commit and the six LSMC release commits through native AlignStats autodetection.
- Merge conflicts: only generated `multiqc/templates/default/compiled/js/multiqc.min.js` and `multiqc/templates/disco/compiled/js/multiqc.min.js`. Both were regenerated from merged sources with `npm ci && npm run build`; no compiled bundle was hand-edited.
- Initial repo state: the fresh clone was clean before branching. The merge commit is complete. New implementation work starts from a clean tracked tree.
- Existing related surfaces: native `alignstats` and `ultima` modules; DayOA source-faithful manifest report generator; DayOA `reported_vs_inferred_sex_check_mqc.tsv` contract.
- Baseline focused check: `.venv/bin/python -m pytest multiqc/modules/alignstats/tests/test_alignstats.py tests/test_ultima_alignstats_parsers.py tests/test_ai_openai_config.py -q` returned `13 passed`.
- Broader baseline boundary: adding `tests/test_custom_content.py` returned `33 passed, 6 failed, 4 errors`. The six failures predate this feature and arise from the fork's intentional duplicate custom-content sample hard-fail behavior. The four errors report the absent external `test-data` checkout.
- Assumptions: `SAMPLEID` is the authoritative sample key. One `units.tsv` row is one library/analysis unit. An explicit `analysis_unit_uid` is authoritative; otherwise the DayOA composite identifier columns are required. Missing schemas, duplicate keys, cross-file mismatches, missing per-unit Hybrid QC rows, and nonnumeric QC values fail hard.
- Live limits: this task changes and verifies local source only. It does not publish a package, tag a release, push a branch, open a PR, or change DayOA runtime inputs.

## Contract Decisions

- Native module key: `snakemake_samples`; report name: `Snakemake Samples`.
- Native inputs:
  - `samples.tsv`, unique `SAMPLEID` rows, shown as `Samples`.
  - `units.tsv`, rows keyed by `analysis_unit_uid` or the strict DayOA composite, shown as `Libraries`.
  - `reported_vs_inferred_sex_check_mqc.tsv`, sample-level reported versus observed evidence, shown as `Reported and Observed Gender Checks`.
  - `hybrid_seq_batch_qc.tsv`, exact per-library observation and threshold input, shown as `Hybrid Seq Batch QC`.
- The Hybrid input will carry measured values and thresholds. MultiQC will compute every individual check and the overall PASS/FAIL itself. It will not trust a precomputed overall result.
- Overall Hybrid PASS requires every check to pass: reported gender matches observed; contamination is strictly below its maximum; short-read coverage percentage and long-read coverage are strictly above their minima; long-read target 10x percentage is strictly above its minimum; short-read low-coverage target percentage is strictly below its maximum; hybrid callable target SNV percentage is strictly above its minimum; uniformity is within inclusive lower and upper bounds; and expected relative matches equal detected relative matches.
- Native benchmark module key: `snakemake_benchmarks`; report name: `Snakemake Benchmarks`.
- The benchmark module accepts exactly one combined `benchmarks.tsv`, `benchmarks_summary.tsv`, or `rules_benchmark_data_mqc.tsv` input with `rule`, `s`, `cpu_time`, `snakemake_threads`, and `task_cost` columns. It reports observed CPU time separately from allocated vCPU time.
- Benchmark aggregate rules strip only a terminal numeric shard suffix such as `.17`, `.1-24`, or `.4~100000001-150000000`; other rule-name components remain authoritative.
- Benchmark formulas: walltime hours = `s / 3600`; observed CPU time hours = `cpu_time / 3600`; allocated vCPU time hours = `s * snakemake_threads / 3600`; task cost = the authoritative input `task_cost`. No proxy price is substituted.
- Actual DayOA evidence adds one explicit producer row type: root-level `*.bench.tsv` rows carry their source path in `sample` and place metrics one column left of sample-scoped rows. The native parser recognizes only that exact shape, labels it `root_benchmark_path`, derives the aggregate rule from the declared benchmark filename, and keeps all other unexpected shapes as hard errors.

## Control Ledger

| ID | Area | Requirement / Surface | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| REL-001 | Release integration | Start from native AlignStats release line and include all current upstream changes | SUCCESS | feature_implementation | Gate 0 | orchestrator | Merge `2fcad4e3`; `HEAD...upstream/main` is `7 0`; focused baseline `13 passed` |  | Current upstream and all LSMC commits through `.6` are ancestors of the branch. |
| MOD-001 | Module registration | Register native `snakemake_samples` entry point and strict search patterns | SUCCESS | feature_implementation | Gate 1 | orchestrator | `pyproject.toml`; native exact-filename patterns precede generic custom content in `multiqc/search_patterns.yaml`. |  | All-module strict render selected both native modules. |
| MAN-001 | Samples | Parse unique `SAMPLEID` rows and render all source columns in Samples | SUCCESS | feature_implementation | Gate 1 | orchestrator | `multiqc/modules/snakemake_samples/`; two-row strict fixture render. |  | Samples section rendered with all source columns. |
| MAN-002 | Libraries | Parse every units row, construct collision-safe analysis unit keys, validate sample references, and render Libraries | SUCCESS | feature_implementation | Gate 1 | orchestrator | Parser tests cover explicit and composite keys, duplicates, and unknown samples. |  | Libraries section rendered for both fixture units. |
| SEX-001 | Gender QC | Parse reported versus inferred evidence, cross-check reported values against samples.tsv, and render sample-level checks | SUCCESS | feature_implementation | Gate 1 | orchestrator | Exact-coverage, provenance-match, and strict-render evidence. |  | Reported and Observed Gender Checks rendered natively. |
| HYB-001 | Hybrid schema | Define and document the exact per-library `hybrid_seq_batch_qc.tsv` schema | SUCCESS | feature_implementation | Gate 1 | orchestrator | Module class docstring and fixture header define schema version 1 and all 22 columns. |  | Schema is explicit and versioned. |
| HYB-002 | Hybrid validation | Require exactly one Hybrid QC row per units row and reject unknown or duplicate units and malformed values | SUCCESS | feature_implementation | Gate 1 | orchestrator | Parser tests exercise empty, malformed, duplicate, unknown, missing, nonfinite, and cross-file mismatch cases. |  | Invalid evidence fails hard. |
| HYB-003 | Hybrid evaluation | Compute nine individual checks plus overall PASS/FAIL with explicit comparison semantics | SUCCESS | feature_implementation | Gate 1 | orchestrator | Boundary and PASS/FAIL tests in `test_parser.py`. |  | Overall status is derived from all nine checks. |
| HYB-004 | Hybrid rendering | Render per-library values, thresholds, check results, overall status, and general-stat summary columns | SUCCESS | feature_implementation | Gate 1 | orchestrator | `/private/tmp/multiqc-snakemake-native-final-20260712/snakemake-native-final.html`. |  | Strict fixture report contains Hybrid detail and general statistics. |
| BEN-001 | Benchmark schema | Parse the combined Snakemake benchmark TSV and fail hard on missing or malformed walltime, CPU, thread, or task-cost evidence | SUCCESS | feature_implementation | Gate 1 | orchestrator | Benchmark parser tests; explicit `NA` or blank optional metric handling retains evidence counts. |  | Required walltime is numeric; missing optional evidence is not converted to zero. |
| BEN-002 | Benchmark aggregation | Normalize terminal shard suffixes and aggregate execution count, walltime, observed CPU time, allocated vCPU time, and task cost per rule | SUCCESS | feature_implementation | Gate 1 | orchestrator | Aggregate-rule and formula tests; actual Batch A report parsed 5,863 rows into 718 aggregate rules. |  | Observed CPU and allocated vCPU remain distinct metrics. |
| BEN-003 | Benchmark rendering | Render aggregate-rule summary statistics and walltime, observed CPU, allocated vCPU, and task-cost boxplots | SUCCESS | feature_implementation | Gate 1 | orchestrator | `/private/tmp/multiqc-snakemake-benchmarks-batch-a-final-20260712/benchmark-batch-a-final.html`. |  | Summary statistics and four boxplots rendered under strict mode. |
| AMD-001 | Plan amendment | Add explicit missing-metric evidence counts and the DayOA root-benchmark-path row type found in the actual Batch A combined report | SUCCESS | plan_amendment | Gate 1 | orchestrator | `rules_benchmark_data_mqc.tsv` has 5,863 rows; 9 rows have `cpu_time=NA` and `snakemake_threads=NA`; root-level benchmark rows place their source path in `sample`. |  | Exact root-path row shape is labeled and parsed; all other unexpected shapes fail. |
| TST-001 | Parser tests | Cover valid, empty, malformed, duplicate, boundary, cross-file, and exact-coverage behavior | SUCCESS | validation | Gate 5 | orchestrator | Final focused command returned `43 passed in 0.96s`. |  | New parser and inherited module tests are green. |
| TST-002 | Native integration | Run module integration and strict MultiQC render against representative inputs | SUCCESS | validation | Gate 5 | orchestrator | Combined all-modules strict render found 3 benchmark rows, 2 rules, 2 samples, 2 libraries, 2 gender checks, and 2 Hybrid rows. |  | Native search precedence is verified, including `_mqc.tsv` inputs. |
| TST-003 | Quality | Run focused tests, ruff, mypy, code checks, and diff checks | SUCCESS | validation | Gate 5 | orchestrator | `ruff check multiqc`, `mypy multiqc`, `.github/workflows/code_checks.py`, and `git diff --check` all passed. |  | Full checked source surface passes repository quality gates. |
| TST-004 | Regression boundary | Re-run the relevant existing AlignStats, AI, custom-content, and module tests; distinguish inherited failures from regressions | SUCCESS | validation | Gate 5 | orchestrator | Focused inherited tests are included in the 43-pass command. Broad run: `13 failed, 251 passed, 5 skipped, 57 errors`. | Existing fork duplicate-sample hard-fail semantics cause the 13 failures; absent external `test-data` causes all 57 errors. Both were reproduced at baseline and are outside these modules. | No new focused regression. Full-suite green is not claimed. |
| DOC-001 | Documentation | Put the native input schemas, comparison rules, and examples in the module class docstring | SUCCESS | documentation | Gate 5 | orchestrator | Class docstrings in both native modules document inputs, formulas, comparisons, row variants, and missing evidence behavior. |  | Documentation ships with the modules. |
| FIN-001 | Final acceptance | Terminalize every row and state whether source objective and publish objective are complete | SUCCESS | validation | Gate 5 | orchestrator | All 19 rows are terminal. |  | Local source objective complete; publication was not requested and did not occur. |

## Final Report

All rows terminal: yes

Objective complete in the authorized local source-change scope: yes

Publish, tag, push, and pull-request objective: not requested; none occurred

Status counts:

- SUCCESS: 19
- OPEN: 0
- IN_PROGRESS: 0
- ATTEMPTING_BUGFIX: 0
- FAIL: 0
- BLOCKED: 0
- DUPLICATE: 0
- NO_LONGER_NEEDED: 0
