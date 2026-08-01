import csv
import io
import logging

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import bargraph, scatter, table
from multiqc.types import SectionAlert

log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    """GIAB concordance summaries produced by DayOA RTG vcfeval workflows."""

    def __init__(self):
        super().__init__(
            name="GIAB concordance",
            anchor="giab-concordance",
            href="https://github.com/RealTimeGenomics/rtg-tools",
            info=("Small-variant and sequence-resolved Jasmine concordance against Genome in a Bottle truth sets"),
            doi=None,
        )

        rtg_data = self.parse_rtg_aggregate()
        jasmine_data = self.parse_jasmine_le50_aggregate()
        if not rtg_data and not jasmine_data:
            raise ModuleNoSamplesFound

        if rtg_data:
            log.info(f"Found {len(rtg_data)} GIAB RTG concordance rows")
            self.add_rtg_sections(rtg_data)
        if jasmine_data:
            log.info(f"Found {len(jasmine_data)} Jasmine <=50 bp RTG concordance rows")
            self.add_jasmine_sections(jasmine_data)

        if rtg_data:
            self.write_data_file(rtg_data, "multiqc_giab_concordance_rtg")
        if jasmine_data:
            self.write_data_file(
                jasmine_data,
                "multiqc_giab_concordance_jasmine_le50",
            )

    @staticmethod
    def parse_number(value, number_type):
        if value in {None, "", ".", "NA", "None"}:
            return None
        if number_type is int:
            parsed = float(value)
            if not parsed.is_integer():
                raise ValueError(f"Expected an integer-valued metric, found {value!r}")
            return int(parsed)
        return number_type(value)

    def parse_rtg_aggregate(self):
        required_fields = {
            "Sample",
            "SampleID",
            "AnalysisUnitUID",
            "ConcordanceStatus",
            "VariantClass",
            "TgtRegionSize",
            "TN",
            "FN",
            "TP",
            "FP",
            "Fscore",
            "Sensitivity-Recall",
            "Specificity",
            "FDR",
            "PPV",
            "Precision",
            "ROI",
            "Aligner",
            "Deduper",
            "SNVCaller",
        }
        integer_fields = {"TgtRegionSize", "TN", "FN", "TP", "FP"}
        float_fields = {
            "Fscore",
            "Sensitivity-Recall",
            "Specificity",
            "FDR",
            "PPV",
            "Precision",
            "AllVarMeanDP",
        }
        data = {}
        for f in self.find_log_files("giabconcordance/rtg"):
            reader = csv.DictReader(io.StringIO(f["f"]), delimiter="\t")
            if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
                raise ValueError(
                    f"Malformed GIAB concordance aggregate {f['fn']}: expected fields {sorted(required_fields)}"
                )
            for raw_row in reader:
                sample = self.clean_s_name(str(raw_row["Sample"]), f)
                if sample in data:
                    raise ValueError(f"Duplicate GIAB concordance row: {sample}")
                row = dict(raw_row)
                for key in integer_fields:
                    row[key] = self.parse_number(raw_row.get(key), int)
                for key in float_fields:
                    if key in row:
                        row[key] = self.parse_number(raw_row.get(key), float)
                status = str(row["ConcordanceStatus"])
                if status not in {"CONFIGURED", "NOT_CONFIGURED"}:
                    raise ValueError(f"Unexpected GIAB concordance status {status!r} for {sample}")
                data[sample] = row
                self.add_data_source(f, section="rtg", s_name=sample)
                self.add_software_version(None, sample)
        return self.ignore_samples(data)

    def parse_jasmine_le50_aggregate(self):
        required_fields = {
            "Sample",
            "SampleID",
            "AnalysisUnitUID",
            "query",
            "ROI",
            "status",
            "TP-base",
            "TP-call",
            "FP",
            "FN",
            "Precision",
            "Sensitivity-Recall",
            "Fscore",
            "query_records",
        }
        integer_fields = {
            "TP-base",
            "TP-call",
            "FP",
            "FN",
            "query_records",
        }
        float_fields = {"Precision", "Sensitivity-Recall", "Fscore"}
        data = {}
        for f in self.find_log_files("giabconcordance/jasmine_le50"):
            reader = csv.DictReader(io.StringIO(f["f"]), delimiter="\t")
            if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
                raise ValueError(
                    f"Malformed Jasmine <=50 bp concordance aggregate {f['fn']}: "
                    f"expected fields {sorted(required_fields)}"
                )
            for raw_row in reader:
                sample = self.clean_s_name(str(raw_row["Sample"]), f)
                if sample in data:
                    raise ValueError(f"Duplicate Jasmine <=50 bp concordance row: {sample}")
                row = dict(raw_row)
                for key in integer_fields:
                    row[key] = self.parse_number(raw_row.get(key), int)
                for key in float_fields:
                    row[key] = self.parse_number(raw_row.get(key), float)
                status = str(row["status"])
                if status not in {"SUCCESS", "DIAGNOSTIC_FAILED"}:
                    raise ValueError(f"Unexpected Jasmine RTG terminal status {status!r} for {sample}")
                data[sample] = row
                self.add_data_source(f, section="jasmine_le50", s_name=sample)
                self.add_software_version(None, sample)
        return self.ignore_samples(data)

    @staticmethod
    def metric_headers():
        return {
            "Precision": {
                "title": "GIAB Precision",
                "description": "Precision against the configured GIAB truth set",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
            "Sensitivity-Recall": {
                "title": "GIAB Recall",
                "description": "Recall against the configured GIAB truth set",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
            "Fscore": {
                "title": "GIAB F1",
                "description": "Harmonic mean of GIAB precision and recall",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
        }

    def add_rtg_sections(self, data):
        configured = {sample: row for sample, row in data.items() if row["ConcordanceStatus"] == "CONFIGURED"}
        summaries = {sample: row for sample, row in configured.items() if row["VariantClass"] == "All"}
        if summaries:
            self.general_stats_addcols(summaries, self.metric_headers())

        not_configured = sorted(
            str(row["SampleID"]) for row in data.values() if row["ConcordanceStatus"] == "NOT_CONFIGURED"
        )
        alerts = []
        if not_configured:
            alerts.append(
                SectionAlert(
                    message=(
                        "GIAB truth was not configured for: "
                        + ", ".join(not_configured)
                        + ". These rows are explicit applicability evidence."
                    ),
                    level="info",
                )
            )

        headers = {
            "SampleID": {
                "title": "Biological sample",
                "description": "Manifest-supplied biological sample identity",
            },
            "ConcordanceStatus": {
                "title": "Status",
                "description": "Whether GIAB truth was configured",
            },
            "VariantClass": {
                "title": "Class",
                "description": "Variant class reported by RTG vcfeval",
            },
            "ROI": {
                "title": "Truth region",
                "description": "Configured GIAB comparison footprint",
            },
            "Aligner": {"title": "Aligner"},
            "Deduper": {"title": "Deduper"},
            "SNVCaller": {"title": "SNV caller"},
            "TP": {
                "title": "TP",
                "description": "True-positive calls",
                "format": "{:,.0f}",
                "scale": "Greens",
            },
            "FP": {
                "title": "FP",
                "description": "False-positive calls",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            "FN": {
                "title": "FN",
                "description": "False-negative truth variants",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            **self.metric_headers(),
            "Specificity": {
                "title": "Specificity",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
            "AllVarMeanDP": {
                "title": "Mean DP",
                "description": "Mean depth across all evaluated variant records",
                "format": "{:.1f}",
                "scale": "Blues",
            },
        }
        self.add_section(
            name="Small-variant concordance",
            anchor="giab-small-variant-concordance",
            description=(
                "Native RTG vcfeval concordance by analysis unit, caller, truth footprint, and variant class."
            ),
            alerts=alerts,
            plot=table.plot(
                data=data,
                headers=headers,
                pconfig={
                    "id": "giab-small-variant-concordance-table",
                    "title": "GIAB: small-variant concordance",
                },
            ),
        )
        self.add_concordance_plots(
            summaries,
            prefix="giab-small-variant",
            title="GIAB small-variant",
            tp_key="TP",
        )

    def add_jasmine_sections(self, data):
        successful = {sample: row for sample, row in data.items() if row["status"] == "SUCCESS"}
        failed = {sample: row for sample, row in data.items() if row["status"] == "DIAGNOSTIC_FAILED"}
        if successful:
            self.general_stats_addcols(successful, self.metric_headers())

        alerts = []
        if failed:
            alerts.append(
                SectionAlert(
                    message=(
                        "Jasmine <=50 bp RTG diagnostics failed for: "
                        + ", ".join(sorted(str(row["ROI"]) for row in failed.values()))
                        + ". See the retained terminal receipts and logs."
                    ),
                    level="warning",
                )
            )
        headers = {
            "SampleID": {
                "title": "Biological sample",
                "description": "Manifest-supplied biological sample identity",
            },
            "ROI": {
                "title": "Truth region",
                "description": "Configured GIAB comparison footprint",
            },
            "status": {
                "title": "Status",
                "description": "Terminal diagnostic status",
            },
            "query_records": {
                "title": "Query records",
                "description": "Sequence-resolved Jasmine records no longer than 50 bp",
                "format": "{:,.0f}",
                "scale": "Blues",
            },
            "TP-base": {
                "title": "TP truth",
                "description": "Truth records matched by the Jasmine query",
                "format": "{:,.0f}",
                "scale": "Greens",
            },
            "TP-call": {
                "title": "TP Jasmine",
                "description": "Jasmine query records matched to truth",
                "format": "{:,.0f}",
                "scale": "Greens",
            },
            "FP": {
                "title": "FP",
                "description": "Jasmine query records not matched to truth",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            "FN": {
                "title": "FN",
                "description": "Truth variants not matched by Jasmine",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            **self.metric_headers(),
        }
        self.add_section(
            name="Jasmine <=50 bp concordance",
            anchor="giab-jasmine-le50-concordance",
            description=(
                "Diagnostic RTG vcfeval comparison of sequence-resolved Jasmine "
                "calls no longer than 50 bp against GIAB small-variant truth."
            ),
            alerts=alerts,
            plot=table.plot(
                data=data,
                headers=headers,
                pconfig={
                    "id": "giab-jasmine-le50-concordance-table",
                    "title": "GIAB: Jasmine <=50 bp concordance",
                },
            ),
        )
        self.add_concordance_plots(
            successful,
            prefix="giab-jasmine-le50",
            title="GIAB Jasmine <=50 bp",
            tp_key="TP-call",
        )

    def add_concordance_plots(self, data, *, prefix, title, tp_key):
        complete = {
            sample: row
            for sample, row in data.items()
            if all(row.get(key) is not None for key in (tp_key, "FP", "FN", "Precision", "Sensitivity-Recall"))
        }
        if not complete:
            return

        bar_data = {sample: {"TP": row[tp_key], "FP": row["FP"], "FN": row["FN"]} for sample, row in complete.items()}
        self.add_section(
            name=f"{title} classifications",
            anchor=f"{prefix}-classifications",
            description="True-positive, false-positive, and false-negative calls.",
            plot=bargraph.plot(
                bar_data,
                {
                    "TP": {"name": "TP", "color": "#1B9E77"},
                    "FP": {"name": "FP", "color": "#D95F02"},
                    "FN": {"name": "FN", "color": "#7570B3"},
                },
                {
                    "id": f"{prefix}-classifications-plot",
                    "title": f"{title}: classifications",
                    "ylab": "Variant records",
                    "tt_suffix": " records",
                },
            ),
        )

        scatter_data = {
            sample: {
                "x": row["Precision"] * 100,
                "y": row["Sensitivity-Recall"] * 100,
            }
            for sample, row in complete.items()
        }
        self.add_section(
            name=f"{title} precision vs. recall",
            anchor=f"{prefix}-precision-recall",
            description="Precision and recall against the configured GIAB truth set.",
            plot=scatter.plot(
                scatter_data,
                {
                    "id": f"{prefix}-precision-recall-plot",
                    "title": f"{title}: precision vs. recall",
                    "xlab": "Precision (%)",
                    "ylab": "Recall (%)",
                    "xmin": 0,
                    "xmax": 100,
                    "ymin": 0,
                    "ymax": 100,
                    "square": True,
                    "marker_size": 7,
                    "tt_label": ("{point.x:.2f}% precision<br/>{point.y:.2f}% recall"),
                },
            ),
        )
