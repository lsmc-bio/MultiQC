#!/usr/bin/env bash
set -euo pipefail

export DAYOA_AGENT_ID="codex-multiqc-orchestrator-20260713"
export DAYOA_AGENT_KIND="codex-primary"
export DAYOA_HUMAN_REQUESTOR="jmajor"
export DAYOA_TMUX_SESSION="multiqc-hg003-1x-final-20260713"
export DAYOA_LEDGER_PATH="/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712/docs/plans/20260713T161440Z_hg003_1x_hiomrs_whole_tree_multiqc_ledger.md"

analysis_root="/fsx/analysis_results/sent-hg003-5x-0712/hg003-1x-ks-1030-20260713T092619Z/daylily-omics-analysis/results/day/hg38"
reports="$analysis_root/reports"
destination="s3://lsmc-ssf-sequencing-data/derived/dayoa_input_staging/20260713T125855Z_bjuice_prevalidation_hiomrs_1038/multiqc_unpublished/hg003-1x-ks-1030-20260713T092619Z/6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517/report_copy"
intent="Export the validated DAY_fin_new_multiqc artifacts for the requested local copy"

if [[ "${DAYOA_EXPORT_GUARDED:-0}" != "1" ]]; then
  dyec analysis visit \
    --analysis-root "$analysis_root" \
    --mode export \
    --intent "$intent" \
    --human-requestor "$DAYOA_HUMAN_REQUESTOR"
  exec dyec analysis guard \
    --analysis-root "$analysis_root" \
    --operation export \
    --intent "$intent" \
    --human-requestor "$DAYOA_HUMAN_REQUESTOR" \
    -- env DAYOA_EXPORT_GUARDED=1 "$0"
fi

sha256sum --check --strict <<EOF
51a9694608b714de3b7c2638c9b899d83035fc1920c95bc1d8ab9a32eb07a763  $reports/DAY_fin_new_multiqc.html
8e3488708df6dd4070e7136058a877eb27f36173fafcd0976bea7d7219270a15  $reports/DAY_fin_new_multiqc_data/multiqc_data.json
3afe2e0a981d3c4f2a589abd6b657675665bbac713105812c5253b6c4cb79c2d  $reports/DAY_fin_new_multiqc_input_inventory.tsv
07cef5a1ce41561c376182291d2eca4417196712930e75a445e1a22c1c1cb30f  $reports/DAY_fin_new_multiqc_benchmark_rejections.tsv
c85208367dd349bead5c1aa7f580028441f3d6633b7b5e033d8cdb63fcfb2363  $reports/DAY_fin_new_multiqc_adoption.md
EOF

aws s3 cp "$reports/DAY_fin_new_multiqc.html" "$destination/DAY_fin_new_multiqc.html" --only-show-errors
aws s3 sync "$reports/DAY_fin_new_multiqc_data" "$destination/DAY_fin_new_multiqc_data" --only-show-errors
aws s3 cp \
  "$reports/DAY_fin_new_multiqc_input_inventory.tsv" \
  "$destination/DAY_fin_new_multiqc_input_inventory.tsv" \
  --only-show-errors
aws s3 cp \
  "$reports/DAY_fin_new_multiqc_benchmark_rejections.tsv" \
  "$destination/DAY_fin_new_multiqc_benchmark_rejections.tsv" \
  --only-show-errors
aws s3 cp \
  "$reports/DAY_fin_new_multiqc_adoption.md" \
  "$destination/DAY_fin_new_multiqc_adoption.md" \
  --only-show-errors

printf 'EXPORTED_REPORT_COPY=%s\n' "$destination"
