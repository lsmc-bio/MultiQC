# Six-Manifest Native MultiQC Test Evidence

## Candidate

- Worktree: `/Users/jmajor/projects/lsmc/MultiQC`
- Branch: `codex/six-manifest-native-multiqc`
- Base tag: `1.36.dev0-lsmc.9`
- Base release commit: `421bab7a9b02d847da280e8d287f169adef7ce56`

## Focused tests and coverage

```text
coverage run --source=multiqc/modules/snakemake_samples -m pytest -q multiqc/modules/snakemake_samples/tests
42 passed in 4.21s

parser.py                 271 statements, 17 missed, 94%
snakemake_samples.py      188 statements, 3 missed, 98%
total                     717 statements, 20 missed, 97%
```

`ruff check multiqc/modules/snakemake_samples` passed. `ruff format --check`
and `git diff --check` passed after formatting.

## Strict render

The committed `tests/data/six_manifest/` fixture contains one specimen, one
sample, three physical libraries, three sequencing inputs, one analysis unit,
and three ordered input-selection links.

```text
multiqc multiqc/modules/snakemake_samples/tests/data/six_manifest \
  -m snakemake_samples --strict --force \
  --outdir /tmp/multiqc-six-manifest-a4-render \
  --filename six_manifest.html

snakemake_samples | Found 1 specimens, 1 samples, 3 libraries,
3 sequencing inputs, 1 analysis units, 3 analysis-unit input links,
0 gender checks, and 0 Hybrid Seq QC rows
multiqc | MultiQC complete
```

The data directory contained the six entity/link exports plus input provenance.
The analysis-unit download preserved the declared selection order and exact
`MODALITY` and `LAYOUT` values.

## Browser QA

The strict-rendered report was served on loopback and inspected in Chromium
using Playwright CLI. The snapshot exposed all six native sections and exact
row keys. Console result:

```text
Total messages: 1 (Errors: 0, Warnings: 0)
```

The sole message was a browser verbose autocomplete suggestion, not a report
warning or error.

## Broader-suite baseline comparison

The external MultiQC `test-data` repository was subsequently cloned at commit
`84dc905`. The broad search/module harness was run against both the candidate
and an isolated exact `.9` baseline worktree:

```text
candidate acecb8fc: 382 passed, 53 failed
baseline  421bab7a: 340 passed, 53 failed
```

The candidate adds exactly 42 passing native six-manifest tests. The identical
53 failures are inherited from `.9`: fork-wide strict duplicate-source checks,
the pre-existing AlignStats malformed fixture, and LSMC-only modules absent
from the upstream fixture repository. No new broad-harness failure was added by
this change.
