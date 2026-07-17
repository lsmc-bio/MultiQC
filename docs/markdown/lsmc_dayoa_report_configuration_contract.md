# LSMC DayOA report configuration contract

DayOA owns the semantic ordering and default column visibility of its reports.
The MultiQC fork already provides the required configuration interfaces. No
report-specific ordering or provenance-column names belong in the template or
JavaScript.

This contract preserves every staged row and every exported column. A hidden
column is hidden only in the initial browser view. It remains available through
Configure Columns and in the complete table download.

## Meaningful section hierarchy

Use all three configuration layers together:

- `module_order` lists every expected native module. Modules omitted from this
  list are placed above listed modules when discovered, which can break the
  intended narrative.
- Each custom table declares the appropriate `parent_id` and `parent_name` in
  `custom_data`.
- `report_section_order` orders native module anchors and custom parent
  anchors. Higher numeric values render earlier in the report.

Do not use `top_modules` for this report. A module cannot be present in both
`top_modules` and `module_order`.

DayOA should use stable custom parent anchors for the requested hierarchy:

| Render order | Parent anchor | Visible title |
| ---: | --- | --- |
| 1 | `dayoa_batch_overview` | Batch Overview |
| 2 | `dayoa_sequencer_reads_qc` | Sequencer Reads and Read QC |
| 3 | `dayoa_alignment_coverage` | Alignment, Sort/Dedup, and Coverage |
| 4 | `dayoa_contamination_identity` | Contamination, Metagenomics, and Identity |
| 5 | `dayoa_variant_calling` | Variant Calling |
| 6 | `dayoa_relatedness_pedigree` | Relatedness and Pedigree |
| 7 | `dayoa_pipeline_delivery` | Pipeline Inputs, Deliverables, Benchmarks, Costs, and Provenance |
| 8 | `multiqc_software_versions` | Software Versions |

A valid descending weight scheme is:

```yaml
report_section_order:
  dayoa_batch_overview: {order: 8000}
  dayoa_sequencer_reads_qc: {order: 7000}
  dayoa_alignment_coverage: {order: 6000}
  dayoa_contamination_identity: {order: 5000}
  dayoa_variant_calling: {order: 4000}
  dayoa_relatedness_pedigree: {order: 3000}
  dayoa_pipeline_delivery: {order: 2000}
  multiqc_software_versions: {order: 1000}
```

Native module anchors must receive weights inside the corresponding band. For
example, FastQC belongs between 7000 and 6990, while Samtools, Picard, Qualimap,
Mosdepth, and Goleft Indexcov belong between 6000 and 5900. Custom subsections
can be reordered within their parent module, but MultiQC does not move a native
module subsection under an unrelated custom parent.

The audited DayOA configuration uses `dayoa_workflow_reporting: 9000` and read
QC values near `1000`. Because higher values render first, that configuration
places workflow reporting ahead of read QC and must be corrected in DayOA.

## Path and provenance columns

Use exact table IDs and exact column IDs. Keep measurements, statuses,
concordance, and QC decisions at weights below `1000`. Move identifiers and
tool context after the measurements. Move filesystem paths, artifact lists,
source coverage evidence, and raw payloads to weights of `8000` or greater and
hide them by default.

```yaml
table_columns_placement:
  alignment_qc_outputs:
    status: 100
    exists: 110
    size_bytes: 120
    source_path: 9000
  contamination:
    gatk_status: 100
    gatk_contamination_pct: 110
    site_mix_status: 120
    site_mix_contamination_pct: 130
    source_coverage_evidence: 8800
    gatk_source_path: 9000
    site_mix_source_path: 9010
  hiomrs_outputs:
    status: 100
    total_files: 110
    total_size_bytes: 120
    core_artifacts: 9000
    segdup_artifacts: 9010
    expansionhunter_artifacts: 9020
    metrics_files: 9030
    result_root: 9040

table_columns_visible:
  alignment_qc_outputs:
    source_path: false
  contamination:
    source_coverage_evidence: false
    gatk_source_path: false
    site_mix_source_path: false
  hiomrs_outputs:
    core_artifacts: false
    segdup_artifacts: false
    expansionhunter_artifacts: false
    metrics_files: false
    result_root: false
```

Apply the same rule to these audited provenance columns:

- Output inventories: `source_path`, `result_root`, `core_artifacts`,
  `segdup_artifacts`, `expansionhunter_artifacts`, and `metrics_files`.
- Contamination and identity: `gatk_source_path`, `site_mix_source_path`,
  `source_path`, `raw_payload`, and `source_coverage_evidence`.
- Variant outputs: `vcf_path`, `vcf_gz`, `summary_glob`, `json_path`,
  `tsv_path`, `done_path`, `output_paths`, `primary_path`,
  `sentieon_primary_path`, and `smncopynumbercaller_primary_path`.
- Sex-complement evidence: `source_alignment`, `source_index`,
  `reference_fasta`, `library_metadata_path`, `somalier_sites_vcf`, and
  `somalier_sites_index`.
- Benchmark rejections and staging provenance: `source_path`, `staged_path`,
  `source_filename`, `source_sha256`, `raw_text`, and
  `source_coverage_evidence`.

Do not hide `Sample`, `SampleID`, `AnalysisUnitUID`, EUID columns, QC status,
concordance, package readiness, or actual delivery state. Eligibility and
actual R2 delivery must remain separate visible fields.

## Native-module audit

Custom tables remain necessary when they add DayOA grain, modality, caller,
lineage, cross-tool status, or cardinality reconciliation. A native module is
the preferred primary tool display when DayOA already stages a supported native
artifact. The custom table can remain as contextual summary or inventory.

| DayOA evidence | Native MultiQC support | Decision |
| --- | --- | --- |
| FastQC, Samtools, Picard, Qualimap, Mosdepth, Goleft Indexcov | Yes, currently staged | Keep native displays. Keep output inventories only for declared artifact coverage; hide their paths by default. |
| bcftools stats | Yes, currently staged | Keep native bcftools plots. Keep the caller-aware custom summary because it preserves DayOA dimensions. |
| Peddy | Yes, currently staged | Keep native Peddy. Keep the custom status table because it carries DayOA caller and check disposition. |
| Somalier | Yes, currently staged | Keep native sample and pair tables. Keep distinct SR and LR summaries because they add modality and relationship counts. |
| Kraken, Ganon, Sourmash | Yes, currently staged when enabled | Keep native displays and retain custom read-set summaries and provenance. |
| VEP | Yes, summary HTML is staged | Keep native VEP. Keep the custom inventory for declared annotated outputs; hide paths and globs. |
| Haplocheck | Yes, source reports are staged | Add `haplocheck` to DayOA `module_order` and order it in the contamination band. Keep the custom cross-evidence table. |
| SeqFu | Yes, but not for the current artifact | The native module parses standard SeqFu stats TSV. DayOA currently requests SeqFu `--multiqc`, which emits custom content. Do not relabel that artifact as native. A future producer change may emit both formats and validate equal sample cardinality. |
| Truvari | Yes, for `truvari bench` logs containing the Stats JSON block | DayOA currently stages its ROI-aware custom aggregate, not the native-compatible benchmark log. Native Truvari is a supplementary candidate after exact log staging and duplicate-ID validation. Do not replace the ROI aggregate. |
| RTG vcfeval and RTG vcfstats | No applicable native module | Keep custom GIAB and RTG sections. The hap.py module is not a parser for RTG output. |
| TIDDIT | No native module | Keep the custom SV summary. |
| ExpansionHunter | No native module | Keep the locus-grain custom section. |
| Sentieon HIOMRS, SegDup, and SMN12 orthogonal evidence | No native module | Keep custom sections. Remove the nonexistent `sentieon` item from DayOA `module_order`; Sentieon-formatted Picard metrics still belong to the Picard module. |
| GATK CalculateContamination and site-mix | No applicable native GATK parser | Keep the DayOA contamination pivot and source-specific evidence. |
| Snakemake samples and benchmarks | Yes, currently configured | Keep native modules. DayOA 12 must update the sample module path filters from the retired `units.tsv` to `specimens.tsv`, `samples.tsv`, and `libraries.tsv`. |

Before adopting any supplementary native module, validate staged-to-rendered
cardinality using the existing `MultiQCAnalysisID` manifest. Native adoption
must not replace or weaken the repaired custom-content collision contract.

## Browser acceptance checklist

Run browser acceptance against a strict-mode report containing SR, LR, hybrid,
and global records. Preserve screenshots and the print PDF outside the release
commit.

- Confirm the approved compact LSMC logo is the rightmost item in the upper
  report header for `lsmc`, `dark`, `light`, and `nosee`. Do not recolor either
  source asset.
- Confirm print rendering uses the black compact logo on a white background,
  including when the interactive report was in `lsmc` or `dark` mode.
- Measure selector-panel text before and after the release. Every
  selector-specific size must be exactly 1 pt smaller; report titles, tables,
  navigation, and other global type must be unchanged.
- Confirm modality counts for the four-record acceptance fixture: All `4/4`,
  SR `2/4`, LR `2/4`, and Hybrid `2/4` because the global record remains
  visible. Confirm the specimen filter shows `3/4`.
- Activate a modality with the keyboard and verify `aria-pressed` and the live
  status text. Confirm a full table export still contains all four records
  while the display is filtered.
- Require zero browser-console errors and warnings. Informational and verbose
  messages may be recorded separately but are not console failures.
