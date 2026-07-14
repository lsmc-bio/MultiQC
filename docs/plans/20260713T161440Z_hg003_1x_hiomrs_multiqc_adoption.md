# HG003 1x HIOMRS MultiQC adoption

## Proven build

- Repository: `/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712`
- Branch: `codex/snakemake-samples-hybrid-qc`
- Base/HEAD commit: `2fcad4e380de1d620844837c8913b935ef957a6f`
- Dirty source fingerprint: `6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517`
- Wheel: `multiqc-1.36.dev0-py3-none-any.whl`
- Wheel SHA-256: `df4f2eaba4d5bef32edd5f7f5b15277d6ed9addc864c543e7c1c23dfc4b18c82`
- Wheel URI: `s3://lsmc-ssf-sequencing-data/derived/dayoa_input_staging/20260713T125855Z_bjuice_prevalidation_hiomrs_1038/multiqc_unpublished/hg003-1x-ks-1030-20260713T092619Z/6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517/multiqc-1.36.dev0-py3-none-any.whl`
- Headnode environment: `/home/ubuntu/.local/share/multiqc-hg003-1x-conda-eab70e9a`
- Cloned dependency environment: `/fsx/resources/environments/conda/ubuntu/ip-10-0-0-203/81c53d718baabdece1569dd9199a3adf_`
- Generated live-config SHA-256: `94177f5271c0adbdcde6257f39b71587a97859c6423c5b7aac0045cd23e2fa2c`

The fingerprint covers the binary diff from the recorded commit plus all untracked files under `multiqc/**`; it is the immutable identity of the unpublished source installed for this report.

## Install the exact wheel

Run as `ubuntu` on the headnode. Do not install this unpublished wheel into the shared DayOA environment.

```bash
wheel_uri='s3://lsmc-ssf-sequencing-data/derived/dayoa_input_staging/20260713T125855Z_bjuice_prevalidation_hiomrs_1038/multiqc_unpublished/hg003-1x-ks-1030-20260713T092619Z/6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517/multiqc-1.36.dev0-py3-none-any.whl'
wheel=/home/ubuntu/multiqc-6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517.whl
env=/home/ubuntu/.local/share/multiqc-hg003-1x-conda-eab70e9a
base_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-203/81c53d718baabdece1569dd9199a3adf_

aws s3 cp "$wheel_uri" "$wheel" --only-show-errors
printf '%s  %s\n' 'df4f2eaba4d5bef32edd5f7f5b15277d6ed9addc864c543e7c1c23dfc4b18c82' "$wheel" | sha256sum --check --strict
test -x "$env/bin/python" || conda create --yes --prefix "$env" --clone "$base_env"
"$env/bin/python" -m pip install --no-deps --force-reinstall "$wheel"
"$env/bin/multiqc" --version
```

## Reproduce the accepted render

The durable renderer is `docs/plans/20260713T161440Z_render_hg003_1x_multiqc.sh`. It rebuilds the validated native-module configuration from the live DayOA configuration, verifies the wheel, installs it into the dedicated environment, excludes prior MultiQC outputs and superseded inputs, and runs MultiQC with `--strict`.

On cluster `sent-hg003-5x-0712`, in the persistent interactive `ubuntu` tmux session:

```bash
bash /home/ubuntu/multiqc-hg003-1x-render-20260713/render_hg003_1x_multiqc.sh
```

Accepted scratch outputs:

- `/home/ubuntu/multiqc-hg003-1x-render-20260713/output/DAY_fin_new_multiqc.html`
- `/home/ubuntu/multiqc-hg003-1x-render-20260713/output/DAY_fin_new_multiqc_data/`
- `/home/ubuntu/multiqc-hg003-1x-render-20260713/DAY_fin_new_multiqc_input_inventory.tsv`
- `/home/ubuntu/multiqc-hg003-1x-render-20260713/benchmark_rejections.tsv`

The strict render exited zero. Its HTML SHA-256 is `51a9694608b714de3b7c2638c9b899d83035fc1920c95bc1d8ab9a32eb07a763`; its `multiqc_data.json` SHA-256 is `8e3488708df6dd4070e7136058a877eb27f36173fafcd0976bea7d7219270a15`.

The browser smoke test loaded the report with no JavaScript errors or warnings, navigated to the native Snakemake Samples section, and confirmed the expected Samples, Libraries, gender, benchmark walltime, vCPU-time, and cost sections. Disabled AI summaries select the explicit `none` provider; an enabled provider continues to use the environment-derived model configuration.

## Expected native content

- Snakemake Samples: one `HG003` sample, one library/unit, and one reported-versus-observed gender check (`male` versus `XY`, `PASS`). Raw and staged manifests are required to normalize identically; all source paths are retained in provenance.
- AlignStats: two assay-qualified reports, `hiomrs_sr.na` and `hiomrs_lr.na`, reconciled across native and combined sources.
- Snakemake Benchmarks: 130 valid benchmark rows across 127 aggregate rules, with walltime, vCPU time, and cost boxplots plus tabular summaries. Eighteen malformed path-shifted rows are rejected explicitly in `benchmark_rejections.tsv`.
- Somalier: separate SR and LR measurements are retained as assay-qualified rows.
- Hybrid Seq Batch QC: unavailable for this run because no valid `hybrid_seq_batch_qc.tsv` producer output exists. No thresholds or pass/fail values were synthesized.
- Existing stock and DayOA custom sections remain enabled. Prior `*_multiqc.html` and `*_multiqc_data` outputs are excluded.

## Release boundary

This is a proven but unpublished build. It has not been committed, pushed, tagged, published to a package index, or substituted into either DayOA `1.36.dev0-lsmc.6` pin. A separate authorized release task may commit the implementation, create the next non-`v` annotated release tag, publish it, and then update both DayOA environment pins after independent live proof.
