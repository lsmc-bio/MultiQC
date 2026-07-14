#!/usr/bin/env bash
set -euo pipefail

export DAYOA_AGENT_ID="codex-multiqc-orchestrator-20260713"
export DAYOA_AGENT_KIND="codex-primary"
export DAYOA_HUMAN_REQUESTOR="jmajor"
export DAYOA_TMUX_SESSION="multiqc-hg003-1x-final-20260713"
export DAYOA_LEDGER_PATH="/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712/docs/plans/20260713T161440Z_hg003_1x_hiomrs_whole_tree_multiqc_ledger.md"

analysis_root="/fsx/analysis_results/sent-hg003-5x-0712/hg003-1x-ks-1030-20260713T092619Z/daylily-omics-analysis/results/day/hg38"
reports="$analysis_root/reports"
scratch="/home/ubuntu/multiqc-hg003-1x-render-20260713"
intent="Publish validated DAY_fin_new_multiqc report, data, inventory, rejection ledger, and adoption guide"

publish_payload="$scratch/publish_payload.sh"
test -x "$publish_payload"

dyec analysis visit \
  --analysis-root "$analysis_root" \
  --mode write \
  --intent "$intent" \
  --human-requestor "$DAYOA_HUMAN_REQUESTOR"

dyec analysis lock acquire \
  --analysis-root "$analysis_root" \
  --operation write \
  --intent "$intent" \
  --human-requestor "$DAYOA_HUMAN_REQUESTOR" \
  --command-summary "publish DAY_fin_new_multiqc artifacts" \
  --operation-scope "reports/DAY_fin_new_multiqc*"

release_lock() {
  dyec analysis lock release \
    --analysis-root "$analysis_root" \
    --human-requestor "$DAYOA_HUMAN_REQUESTOR" \
    --note "DAY_fin_new_multiqc publication finished"
}
trap release_lock EXIT

dyec analysis guard \
  --analysis-root "$analysis_root" \
  --operation write \
  --intent "$intent" \
  --human-requestor "$DAYOA_HUMAN_REQUESTOR" \
  -- "$publish_payload"

sha256sum \
  "$reports/DAY_final_multiqc.html" \
  "$reports/DAY_final_multiqc_data/multiqc_data.json" \
  "$reports/DAY_fin_new_multiqc.html" \
  "$reports/DAY_fin_new_multiqc_data/multiqc_data.json" \
  "$reports/DAY_fin_new_multiqc_input_inventory.tsv" \
  "$reports/DAY_fin_new_multiqc_benchmark_rejections.tsv" \
  "$reports/DAY_fin_new_multiqc_adoption.md"

release_lock
trap - EXIT
