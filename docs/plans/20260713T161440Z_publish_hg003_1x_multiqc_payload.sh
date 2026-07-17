#!/usr/bin/env bash
set -euo pipefail

analysis_root="/fsx/analysis_results/sent-hg003-5x-0712/hg003-1x-ks-1030-20260713T092619Z/daylily-omics-analysis/results/day/hg38"
reports="$analysis_root/reports"
scratch="/home/ubuntu/multiqc-hg003-1x-render-20260713"

targets=(
  "$reports/DAY_fin_new_multiqc.html"
  "$reports/DAY_fin_new_multiqc_data"
  "$reports/DAY_fin_new_multiqc_input_inventory.tsv"
  "$reports/DAY_fin_new_multiqc_benchmark_rejections.tsv"
  "$reports/DAY_fin_new_multiqc_adoption.md"
)
existing_count=0
for target in "${targets[@]}"; do
  [[ ! -e "$target" ]] || existing_count=$((existing_count + 1))
done
if [[ "$existing_count" -ne 0 && "$existing_count" -ne "${#targets[@]}" ]]; then
  printf 'Refusing partial publication update: %s of %s targets exist\n' "$existing_count" "${#targets[@]}" >&2
  exit 1
fi
if [[ "$existing_count" -eq "${#targets[@]}" ]]; then
  # The first accepted publication exposed a disabled-AI browser initialization
  # error. Only that exact agent-owned publication may be replaced in place.
  sha256sum --check --strict <<EOF
86c1d77ff11c1760b9134437f9c8e1916466ca883965b0fc26407ef8a09aa5cd  $reports/DAY_fin_new_multiqc.html
4df89f962d5e7ca267666eabc0eb778e621729bdc24e58685f585341fb1b819b  $reports/DAY_fin_new_multiqc_data/multiqc_data.json
3afe2e0a981d3c4f2a589abd6b657675665bbac713105812c5253b6c4cb79c2d  $reports/DAY_fin_new_multiqc_input_inventory.tsv
07cef5a1ce41561c376182291d2eca4417196712930e75a445e1a22c1c1cb30f  $reports/DAY_fin_new_multiqc_benchmark_rejections.tsv
0c21feaa52118507cafd0bb4c14654dbd48c675955a64f2ba234717152dbb941  $reports/DAY_fin_new_multiqc_adoption.md
EOF
fi

install -m 0644 "$scratch/output/DAY_fin_new_multiqc.html" "$reports/DAY_fin_new_multiqc.html"
if [[ -d "$reports/DAY_fin_new_multiqc_data" ]]; then
  cp -a "$scratch/output/DAY_fin_new_multiqc_data/." "$reports/DAY_fin_new_multiqc_data/"
else
  cp -a "$scratch/output/DAY_fin_new_multiqc_data" "$reports/DAY_fin_new_multiqc_data"
fi
install -m 0644 \
  "$scratch/DAY_fin_new_multiqc_input_inventory.tsv" \
  "$reports/DAY_fin_new_multiqc_input_inventory.tsv"
install -m 0644 \
  "$scratch/benchmark_rejections.tsv" \
  "$reports/DAY_fin_new_multiqc_benchmark_rejections.tsv"
install -m 0644 \
  "$scratch/DAY_fin_new_multiqc_adoption.md" \
  "$reports/DAY_fin_new_multiqc_adoption.md"
