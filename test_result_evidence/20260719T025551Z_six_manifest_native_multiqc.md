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

## Broader-suite environment boundary

`tests/test_search_files.py` and `tests/test_modules_run.py` could not run in
this isolated worktree because the required MultiQC `test-data` checkout is not
present. The fixture reported:

```text
FileNotFoundError: The test data directory expected to be found at
/Users/jmajor/projects/lsmc/MultiQC/test-data
```

No product failure was observed in that attempt. Full repository QA remains an
integration-lane gate once the external test-data fixture is available.
