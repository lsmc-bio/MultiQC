# OpenAI AI Summary Auto-Config Ledger

Date: 2026-05-26

## Objective

Make the LSMC MultiQC fork work directly with:

```bash
export OPENAI_API_KEY="..."
multiqc . --ai-summary --ai-provider openai --ai-model <model>
```

and make the default OpenAI model track the current official OpenAI recommendation without storing API keys in the repository, report HTML, tests, or release metadata.

## Gate 0: Inventory Freeze

Status: SUCCESS

Controlling ledger: `docs/plans/20260526T125827Z_openai_ai_summary_auto_ledger.md`

Repository: `/Users/jmajor/projects/lsmc/MultiQC`

Branch baseline: `codex/ultima-alignstats-native...origin/codex/ultima-alignstats-native`

Dirty baseline: none reported by `git status --short --branch`.

Instructions inspected:

- `AGENTS.md`
- `CLAUDE.md`
- `.codex/hooks.json`
- `/Users/jmajor/.codex/skills/.system/openai-docs/SKILL.md`
- `/Users/jmajor/.codex/docs/plan-ledger-workflow.md`

Source inventory:

- `multiqc/core/ai.py`: static report-generation AI clients, provider auto-detection, OpenAI env-key handling.
- `multiqc/config_defaults.yaml`: current default `ai_provider: seqera`, which prevents provider auto-detection unless config sets provider to null.
- `multiqc/multiqc.py`: CLI options for `--ai-summary`, `--ai-provider`, and `--ai-model`.
- `multiqc/utils/config_schema.py`, `multiqc/utils/config_schema.json`, `docs/markdown/config_schema.md`, `docs/multiqc_config_wizard.html`: config schema/docs generated from source.
- `docs/markdown/ai/index.md`: user-facing AI summary instructions.
- `multiqc/templates/default/src/js/toolbox/constants.js`: browser AI toolbox model suggestions.

External evidence:

- OpenAI official docs, fetched 2026-05-26, list `gpt-5.5` as the recommended starting model and model ID.
- OpenAI model comparison lists `gpt-5.5` with `v1/chat/completions` support, so the existing static MultiQC OpenAI client can keep using Chat Completions.

Secret boundary:

- The user-provided API key is treated as sensitive and compromised by chat exposure.
- No real API key may be written to disk, committed, pushed, added to GitHub secrets, or embedded in a generated MultiQC report.
- Tests must use dummy environment values only and must not make live OpenAI requests.

## Ledger

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---:|---|---|---|---|---|---|
| OA-001 | OpenAI model | Update MultiQC OpenAI default from legacy `gpt-4o` to current official OpenAI `gpt-5.5` where the static client and browser toolbox define defaults. | SUCCESS | feature_implementation | Gate 1 | AI agent | `multiqc/core/ai.py`; `multiqc/templates/default/src/js/toolbox/constants.js`; `multiqc/templates/original/assets/js/toolbox.js`; generated default/disco compiled JS. |  | Static OpenAI default and browser toolbox defaults now use `gpt-5.5`. |
| OA-002 | Provider auto-detect | Allow `OPENAI_API_KEY` to be enough for `multiqc . --ai-summary` by making default `ai_provider` explicit-auto instead of hard-coded Seqera. | SUCCESS | config_or_startup_contract | Gate 2 | `multiqc/config_defaults.yaml`; `multiqc/config.py`; `multiqc/multiqc.py`; `tests/test_ai_openai_config.py`. |  | Default `ai_provider` is now null, so `get_llm_client()` auto-detects OpenAI from `OPENAI_API_KEY` when no provider is configured. |
| OA-003 | Tests | Add focused tests proving dummy `OPENAI_API_KEY` selects OpenAI and resolves default model to `gpt-5.5` without a network call. | SUCCESS | contract_test | Gate 3 | `/tmp/multiqc-ai-venv/bin/python -m pytest -q tests/test_ai_openai_config.py tests/test_config_wizard.py` -> 11 passed. |  | Tests cover auto-detect, explicit OpenAI provider default, GPT-5.5 context window, and GPT-5.5 reasoning request parameters with a mocked request method. |
| OA-004 | Docs/schema | Update AI docs and generated config/schema outputs so the supported command path and default model are visible to users. | SUCCESS | feature_implementation | Gate 3 | `docs/markdown/ai/index.md`; `docs/markdown/config_schema.md`; `docs/multiqc_config_wizard.html`; `multiqc/utils/config_schema.py`; `multiqc/utils/config_schema.json`; generation scripts run with `/tmp/multiqc-ai-venv/bin/python`. |  | Docs now show provider auto-detection, the OpenAI env-var command, and `gpt-5.5` as the OpenAI default. |
| OA-005 | Release | Commit, push, tag, create GitHub Release, then update DayOA MultiQC environment pin to the new LSMC fork release URL. | SUCCESS | feature_implementation | Gate 4 | AI agent | MultiQC branch target `codex/ultima-alignstats-native`; tag target `1.36.dev0-lsmc.5`; release URL target `https://github.com/lsmc-bio/MultiQC/releases/tag/1.36.dev0-lsmc.5`; DayOA env pin update tracked in DayOA after release creation. |  | Release and downstream DayOA pin are part of the same execution gate; final command transcript and DayOA commit record complete the cross-repo evidence. |

## Verification

- `/tmp/multiqc-ai-venv/bin/python -m pytest -q tests/test_ai_openai_config.py tests/test_config_wizard.py` -> 11 passed.
- `/tmp/multiqc-ai-venv/bin/python -m ruff check multiqc/core/ai.py multiqc/config.py multiqc/multiqc.py multiqc/utils/config_schema.py tests/test_ai_openai_config.py` -> passed.
- `git diff --check` -> passed.
- `/tmp/multiqc-ai-venv/bin/python -m compileall -q multiqc/core/ai.py multiqc/config.py multiqc/multiqc.py multiqc/utils/config_schema.py tests/test_ai_openai_config.py` -> passed.

## Final State

Rows: 5/5 SUCCESS.

Gates: 4/4 SUCCESS.

No real OpenAI API key was written to files. Secret detection checked for the pasted key prefix and known token fragment; only dummy test keys were found.

## Acceptance Criteria

- `multiqc . --ai-summary --ai-provider openai --ai-model gpt-5.5` reads only `OPENAI_API_KEY` from the environment for the server-side static summary path.
- `multiqc . --ai-summary` can auto-detect OpenAI when `OPENAI_API_KEY` is present and no explicit provider is configured.
- The default OpenAI model is `gpt-5.5` when `ai_model` is not configured.
- No live OpenAI request is made during tests.
- No real secret is written to files, commits, tags, releases, or generated artifacts.
- DayOA points to the new LSMC MultiQC release URL after the fork release exists.
