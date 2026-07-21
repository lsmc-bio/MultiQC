# OpenAI Default MultiQC Release Ledger

Date: 2026-07-21

## Objective

Release a new LSMC MultiQC tag with OpenAI as the default AI provider,
`gpt-5.6` as the default OpenAI model, and a local token-file environment
bootstrap path that does not embed secrets into generated reports.

## Gate 0 Inventory

- MultiQC repo: `/Users/jmajor/projects/lsmc/MultiQC`
- Starting branch: `codex/six-manifest-native-multiqc`
- Previous MultiQC release tag: `1.36.dev0-lsmc.11`
- New MultiQC release tag: `1.36.dev0-lsmc.12`
- DayOA pin target: `/Users/jmajor/projects/lsmc/daylily-omics-analysis/workflow/envs/multiqc_v0.1.yaml`

## Ledger

| ID | Area | Requirement | Status | Evidence |
|---|---|---|---:|---|
| OAI-001 | Provider default | Make report-generation AI default to OpenAI. | SUCCESS | `multiqc/config_defaults.yaml` sets `ai_provider: openai`. |
| OAI-002 | Model default | Set default OpenAI model to `gpt-5.6`. | SUCCESS | `multiqc/core/ai.py`, browser toolbox source, generated schema/docs, and focused tests updated. |
| OAI-003 | Secret handling | Read a local token file into `OPENAI_API_KEY` before long-running template dev processes without writing the token to HTML or config. | SUCCESS | `scripts/openai-env.sh`; `npm run dev` and `npm run watch` source it before Vite starts. |
| OAI-004 | Validation | Run focused config and AI tests plus lint/build checks. | SUCCESS | `pytest tests/test_ai_openai_config.py tests/test_config_wizard.py` -> 11 passed; `ruff check` -> passed; `npm run build` -> passed; `git diff --check` -> passed. |
| OAI-005 | Release | Commit, push branch, tag `1.36.dev0-lsmc.12`, and push tag. | PENDING | Awaiting commit/tag/push. |
| OAI-006 | DayOA pin | Update DayOA MultiQC conda env to tag `1.36.dev0-lsmc.12`. | PENDING | Awaiting released tag push and DayOA pin commit. |

## Secret Boundary

No OpenAI token value is stored in this repo, generated HTML, generated schema,
docs, tests, commits, or tags. The local token file is read only into the
process environment as `OPENAI_API_KEY`.
