#!/usr/bin/env bash
set -euo pipefail

export DAYOA_AGENT_ID="codex-multiqc-orchestrator-20260713"
export DAYOA_AGENT_KIND="codex-primary"
export DAYOA_HUMAN_REQUESTOR="jmajor"
export DAYOA_TMUX_SESSION="multiqc-hg003-1x-final-20260713"
export DAYOA_LEDGER_PATH="/Users/jmajor/projects/lsmc/multiqc-samples-hybrid-qc-20260712/docs/plans/20260713T161440Z_hg003_1x_hiomrs_whole_tree_multiqc_ledger.md"

ANALYSIS_REPO="/fsx/analysis_results/sent-hg003-5x-0712/hg003-1x-ks-1030-20260713T092619Z/daylily-omics-analysis"
ANALYSIS_ROOT="$ANALYSIS_REPO/results/day/hg38"
SCRATCH="/home/ubuntu/multiqc-hg003-1x-render-20260713"
BASE_ENV="/fsx/resources/environments/conda/ubuntu/ip-10-0-0-203/81c53d718baabdece1569dd9199a3adf_"
SOURCE_FINGERPRINT="6d1b33732b790cd04ce9bdc8e4b06f63b5d0553c81df036b41452ac187a9f517"
WHEEL_SHA256="df4f2eaba4d5bef32edd5f7f5b15277d6ed9addc864c543e7c1c23dfc4b18c82"
WHEEL_NAME="multiqc-1.36.dev0-py3-none-any.whl"
WHEEL_URI="s3://lsmc-ssf-sequencing-data/derived/dayoa_input_staging/20260713T125855Z_bjuice_prevalidation_hiomrs_1038/multiqc_unpublished/hg003-1x-ks-1030-20260713T092619Z/$SOURCE_FINGERPRINT/$WHEEL_NAME"
WHEEL_DIR="$SCRATCH/wheels/$SOURCE_FINGERPRINT"
WHEEL_LOCAL="$WHEEL_DIR/$WHEEL_NAME"
CLONE="/home/ubuntu/.local/share/multiqc-hg003-1x-conda-eab70e9a"
OUTPUT="$SCRATCH/output"
NATIVE_CONFIG="$SCRATCH/multiqc_config_native.yaml"
LOG="$SCRATCH/live_strict_render-$SOURCE_FINGERPRINT.log"

mkdir -p "$SCRATCH" "$WHEEL_DIR"
exec > >(tee "$LOG") 2>&1

if [[ "${MULTIQC_SKIP_INSTALL:-0}" != "1" ]]; then
  aws s3 cp "$WHEEL_URI" "$WHEEL_LOCAL" --only-show-errors
  printf '%s  %s\n' "$WHEEL_SHA256" "$WHEEL_LOCAL" | sha256sum --check --strict

  if [[ ! -x "$CLONE/bin/python" ]]; then
    conda create --yes --prefix "$CLONE" --clone "$BASE_ENV"
  fi
  "$CLONE/bin/python" -m pip install --no-deps --force-reinstall "$WHEEL_LOCAL"
fi
"$CLONE/bin/python" "$SCRATCH/build_native_multiqc_config.py" \
  "$ANALYSIS_REPO/config/external_tools/multiqc_config.yaml" \
  "$NATIVE_CONFIG" \
  --canonical-benchmarks "$SCRATCH/benchmarks.tsv" \
  --analysis-root "$ANALYSIS_ROOT"

"$CLONE/bin/python" - <<'PY'
from importlib.metadata import distributions, entry_points

multiqc_distributions = [dist for dist in distributions() if dist.metadata.get("Name", "").lower() == "multiqc"]
assert len(multiqc_distributions) == 1, multiqc_distributions
targets = {"alignstats", "snakemake_benchmarks", "snakemake_samples", "ultima"}
found = [ep for ep in entry_points().select(group="multiqc.modules.v1") if ep.name in targets]
assert {ep.name for ep in found} == targets, found
assert len(found) == len(targets), found
for ep in sorted(found, key=lambda value: value.name):
    print(f"entry_point={ep.name}:{ep.value}:{ep.dist.name}:{ep.dist.version}")
PY

rm -rf "$OUTPUT"
mkdir -p "$OUTPUT"
cd "$ANALYSIS_REPO"
"$CLONE/bin/multiqc" \
  "$ANALYSIS_ROOT" \
  "$SCRATCH/benchmarks.tsv" \
  --strict \
  --force \
  --config "$ANALYSIS_ROOT/reports/multiqc_header.yaml" \
  --config "$NATIVE_CONFIG" \
  --custom-css-file "$ANALYSIS_REPO/config/external_tools/multiqc.css" \
  --ignore "*/other_reports/logs/*" \
  --ignore "other_reports/logs/*" \
  --ignore "*_mqc.log" \
  --ignore "*_multiqc.html" \
  --ignore "*_multiqc_data" \
  --ignore "native" \
  --ignore "*.ganon2.classify.log" \
  --ignore "input_sample_libraries_mqc.tsv" \
  --ignore "benchmarks_summary.tsv" \
  --ignore "rules_benchmark_data_mqc.tsv" \
  --ignore "reports/*_multiqc.html" \
  --ignore "reports/*_multiqc_data/*" \
  --ignore "*/reports/*_multiqc.html" \
  --ignore "*/reports/*_multiqc_data/*" \
  --ignore "*/reports/benchmarks_summary.tsv" \
  --ignore "*/other_reports/rules_benchmark_data_mqc.tsv" \
  --template default \
  --outdir "$OUTPUT" \
  --filename DAY_fin_new_multiqc.html \
  --title "DAY fin new MultiQC" \
  --comment "Unpublished MultiQC source fingerprint $SOURCE_FINGERPRINT"

test -s "$OUTPUT/DAY_fin_new_multiqc.html"
test -s "$OUTPUT/DAY_fin_new_multiqc_data/multiqc_data.json"
sha256sum "$OUTPUT/DAY_fin_new_multiqc.html" "$OUTPUT/DAY_fin_new_multiqc_data/multiqc_data.json"
printf 'STRICT_RENDER_COMPLETE source_fingerprint=%s wheel_sha256=%s\n' "$SOURCE_FINGERPRINT" "$WHEEL_SHA256"
