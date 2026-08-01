import csv
import io
import json
import logging
import os
import re
from typing import List

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import bargraph, scatter, table
from multiqc.types import SectionAlert

log = logging.getLogger(__name__)


VERSION_REGEX = r"(\d+\.\d+\.[\d\.\-\w]+)"


class MultiqcModule(BaseMultiqcModule):
    """
    Supported commands:

    - `bench`
    """

    def __init__(self):
        super().__init__(
            name="Truvari",
            anchor="truvari",
            href="https://github.com/ACEnglish/truvari",
            info="Benchmarking, merging, and annotating structural variants",
            doi="https://doi.org/10.1101/2022.02.21.481353",
        )

        self._bench_data = {}
        self._dayoa_data = {}
        n = dict()
        n["bench"] = self.parse_bench_stats()
        n["dayoa_aggregate"] = self.parse_dayoa_aggregate()
        if n["bench"] > 0:
            log.info(f"Found {n['bench']} truvari bench reports")
        if n["dayoa_aggregate"] > 0:
            log.info(f"Found {n['dayoa_aggregate']} DayOA Truvari aggregate rows")

        # Exit if we didn't find anything
        if sum(n.values()) == 0:
            raise ModuleNoSamplesFound

        if self._bench_data:
            self.write_data_file(self._bench_data, "multiqc_truvari_bench")
        if self._dayoa_data:
            self.write_data_file(
                self._dayoa_data,
                "multiqc_truvari_dayoa_aggregate",
            )

    def parse_bench_stats(self):
        """Find truvari bench logs and parse their data"""
        data = {}
        for f in self.find_log_files("truvari/bench"):
            inside_json_block = False
            json_text = ""
            version = None
            for line in f["f"].splitlines():
                if "Stats:" in line:
                    inside_json_block = True
                    json_text = "{\n"
                    continue

                if inside_json_block:
                    json_text += line
                    if line.startswith("}"):
                        inside_json_block = False

                # Get version from log
                # Log lines look like:
                #   2022-12-01 18:25:54,715 [INFO] Truvari v4.0.0.dev0+detached
                # or
                #   2022-08-25 00:31:16,781 [INFO] Truvari version: 3.5.0-dev
                if "Truvari" in line:
                    match = re.search(VERSION_REGEX, line)
                    if match:
                        version = match.group(1)

            if not json_text:
                log.warning(f"Could not find the 'Stats' JSON block in file: {f['fn']}")
                continue

            # Load stats
            try:
                stats = json.loads(str(json_text))
            except json.decoder.JSONDecodeError as e:
                log.debug(e)
                log.warning(f"Could not parse the 'Stats' JSON block in file: {f['fn']}")
                continue

            # Use output directory as sample name
            f["s_name"] = os.path.basename(f["root"])
            f["s_name"] = self.clean_s_name(f["s_name"], f, root=os.path.dirname(f["root"]))
            if f["s_name"] in data:
                log.debug(f"Duplicate sample name found! Overwriting: {f['s_name']}")

            # Some stats were renamed in truvari 4.0.0 (commit 6e37058)
            # This renames them back to the old names for backwards compatibility
            if all(key in stats for key in ["TP-call_TP-gt", "TP-call_FP-gt", "TP-call", "call cnt"]):
                stats["TP-comp_TP-gt"] = stats["TP-call_TP-gt"]
                stats["TP-comp_FP-gt"] = stats["TP-call_FP-gt"]
                stats["TP-comp"] = stats["TP-call"]
                stats["comp cnt"] = stats["call cnt"]

            self.add_data_source(f, section="bench")
            data[f["s_name"]] = stats

            self.add_software_version(version, f["s_name"])

        # Filter to strip out ignored sample names
        data = self.ignore_samples(data)

        # Return if no samples
        if len(data) == 0:
            return len(data)

        self._bench_data = data

        # General Stats Table
        bench_headers = dict()
        bench_headers["precision"] = {
            "title": "Precision",
            "description": "Precision of the SV calls. Definition: TP-comp / (TP-comp + FP)",
            "suffix": "%",
            "modify": lambda x: x * 100,
            "placement": 100,
            "max": 100,
            "min": 0,
            "scale": "PRGn",
        }
        bench_headers["recall"] = {
            "title": "Recall",
            "description": "Recall of the SV calls. Definition: TP-base / (TP-base + FN)",
            "suffix": "%",
            "modify": lambda x: x * 100,
            "placement": 101,
            "max": 100,
            "min": 0,
            "scale": "BrBG",
        }
        bench_headers["f1"] = {
            "title": "F1",
            "description": "F1 score of the SV calls. Definition: 2 * ((Recall * Precision) / (Recall + Precision))",
            "suffix": "%",
            "modify": lambda x: x * 100,
            "placement": 102,
            "max": 100,
            "min": 0,
            "scale": "RdYlGn",
        }
        bench_headers["gt_concordance"] = {
            "title": "GT concordance",
            "description": "Genotype concordance. Definition: TP-comp with GT / (TP-comp with GT + TP-comp w/o GT)",
            "scale": "GnBu",
            "suffix": "%",
            "placement": 103,
            "max": 100,
            "min": 0,
            "hidden": True,
            "modify": lambda x: x * 100,
        }

        self.general_stats_addcols(data, bench_headers)

        # Make bar graph
        bar_data: List = [{}, {}, {}, {}]
        for sample, sample_data in data.items():
            # Comp
            bar_data[0][sample] = {
                "TP": sample_data["TP-comp"],
                "FP": sample_data["FP"],
            }
            # Base
            bar_data[1][sample] = {
                "TP": sample_data["TP-base"],
                "FN": sample_data["FN"],
            }
            # TP (comp) GT
            bar_data[2][sample] = {
                "Match": sample_data["TP-comp_TP-gt"],
                "No match": sample_data["TP-comp_FP-gt"],
            }
            # TP (base) GT
            bar_data[3][sample] = {
                "Match": sample_data["TP-base_TP-gt"],
                "No match": sample_data["TP-base_FP-gt"],
            }

        bar_categories = [
            # Comp
            {
                "TP": {"name": "TP", "color": "#648FFF"},
                "FP": {"name": "FP", "color": "#DC267F"},
            },
            # Base
            {
                "TP": {"name": "TP", "color": "#648FFF"},
                "FN": {"name": "FN", "color": "#FFB000"},
            },
            # TP (comp) GT
            {
                "Match": {"name": "Match", "color": "#785EF0"},
                "No match": {"name": "No match", "color": "#FE6100"},
            },
            # TP (base) GT
            {
                "Match": {"name": "Match", "color": "#785EF0"},
                "No match": {"name": "No match", "color": "#FE6100"},
            },
        ]

        bar_config = {
            "id": "truvari-bench-classifications-plot",
            "title": "Truvari: Classifications",
            "ylab": "Counts",
            "tt_suffix": " calls",
            "data_labels": [
                {"name": "Comp", "ylab": "Counts"},
                {"name": "Base", "ylab": "Counts"},
                {"name": "TP (comp) GT", "ylab": "Counts"},
                {"name": "TP (base) GT", "ylab": "Counts"},
            ],
        }

        self.add_section(
            name="Classifications",
            anchor="truvari-bench-classifications",
            description="Bargraph of SV call classifications parsed from the output from `truvari bench`",
            helptext="""
            Bargraph of SV call classifications from the perspectives of the *comp* and
            *base* ("truth") VCFs. Four different groups of calls are shown:
    
            #### Comp
            Compares TP and FP calls in the *comp* VCF relative the *base*. The
            classifications are:
    
            - **TP**: Comp call matches a base call
            - **FP**: Comp call does not match a base call
    
            #### Base
            Compares TP and FN calls in the *base* VCF relative the *comp*. The
            classifications are:
    
            - **TP**: Base call matches a comp call
            - **FN**: Base call does not match a comp call
    
            #### TP (comp) GT
            Compares TP calls in the *comp* VCF relative to the *base* VCF for
            matching genotypes. The classifications are:
    
            - **Match**: TP call in comp has matching genotype in base
            - **No match**: TP call in comp does not have matching genotype in base
    
            #### TP (base) GT
            Compares TP calls in the *base* VCF relative to the *comp* VCF for
            matching genotypes. The classifications are:
    
            - **Match**: TP call in base has matching genotype in comp
            - **No match**: TP call in base does not have matching genotype in comp
    
            For more information, see the [truvari bench wiki](https://github.com/acenglish/truvari/wiki/bench)
            """,
            plot=bargraph.plot(bar_data, bar_categories, pconfig=bar_config),
        )

        # Make scatter plot
        scatter_data = {}
        for i, (sample, sample_data) in enumerate(data.items()):
            scatter_data[sample] = {
                "x": sample_data["precision"] * 100.0,
                "y": sample_data["recall"] * 100.0,
            }

        scatter_config = {
            "id": "truvari-bench-pre-rec-plot",
            "marker_size": 5,
            "height": 560,  # increase height slightly to fit title.
            "ymax": 100,
            "ymin": 0,
            "xmax": 100,
            "xmin": 0,
            "xlab": "Precision (%)",
            "ylab": "Recall (%)",
            "square": True,
            "title": "Truvari: Precision vs. Recall",
            "tt_label": "{point.x:.1f}% precision<br/>{point.y:.1f}% recall",
        }
        self.add_section(
            name="Precision vs. Recall",
            anchor="truvari-bench-pre-rec",
            description="Precision vs. Recall for each sample. Parsed from the output of `truvari bench`",
            helptext="""
            Scatter plot of precision vs. recall comparing SV calls between two VCFs,
            one truth set ("base") and one to be evaluated ("comp"). The precision and
            recall values are calculated as follows:
    
            - **Precision**: TP-comp / (TP-comp + FP)
            - **Recall**: TP-base / (TP-base + FN)
    
            The TP, FP, and FN values are intrun defined as follows:
    
            - **TP (base)**: Number of matching calls from the base ('truth') VCF
            - **TP (comp)**: Number of matching calls from the comp VCF
            - **FP**: Number of non-matching calls from the comp VCF
            - **FN**: Number of non-matching calls from the base ('truth') VCF
    
            For more information, see the [truvari bench wiki](https://github.com/acenglish/truvari/wiki/bench)
            """,
            plot=scatter.plot(scatter_data, scatter_config),
        )

        # Return the number of logs that were found
        return len(data)

    def parse_dayoa_aggregate(self):
        """Parse DayOA terminal-receipt aggregates for named HG002 queries."""
        required_fields = {
            "Sample",
            "SampleID",
            "AnalysisUnitUID",
            "query",
            "status",
            "TP-base",
            "TP-comp",
            "FP",
            "FN",
            "precision",
            "recall",
            "f1",
            "projected_records",
            "excluded_records",
        }
        integer_fields = {
            "TP-base",
            "TP-comp",
            "FP",
            "FN",
            "projected_records",
            "excluded_records",
        }
        float_fields = {"precision", "recall", "f1"}
        data = {}
        for f in self.find_log_files("truvari/dayoa_aggregate"):
            reader = csv.DictReader(io.StringIO(f["f"]), delimiter="\t")
            if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
                raise ValueError(
                    f"Malformed DayOA Truvari aggregate {f['fn']}: expected fields {sorted(required_fields)}"
                )
            for raw_row in reader:
                sample = self.clean_s_name(str(raw_row["Sample"]), f)
                if sample in data:
                    raise ValueError(f"Duplicate DayOA Truvari sample/query row: {sample}")
                row = dict(raw_row)
                for key in integer_fields:
                    if raw_row[key] in {"", "."}:
                        row[key] = None
                    else:
                        parsed = float(raw_row[key])
                        if not parsed.is_integer():
                            raise ValueError(f"Expected integer-valued {key}, found {raw_row[key]!r}")
                        row[key] = int(parsed)
                for key in float_fields:
                    row[key] = None if raw_row[key] in {"", "."} else float(raw_row[key])
                data[sample] = row
                self.add_data_source(f, section="dayoa_aggregate", s_name=sample)
                self.add_software_version(None, sample)

        data = self.ignore_samples(data)
        if not data:
            return 0

        successful = {sample: row for sample, row in data.items() if row["status"] == "SUCCESS"}
        failed = {sample: row for sample, row in data.items() if row["status"] == "DIAGNOSTIC_FAILED"}
        invalid_status = sorted(
            {str(row["status"]) for row in data.values() if row["status"] not in {"SUCCESS", "DIAGNOSTIC_FAILED"}}
        )
        if invalid_status:
            raise ValueError("Unexpected DayOA Truvari terminal status values: " + ", ".join(invalid_status))

        metric_headers = {
            "precision": {
                "title": "Precision",
                "description": "Query-call precision against the GIAB SV truth set",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
            "recall": {
                "title": "Recall",
                "description": "GIAB SV truth recall for the query callset",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
            "f1": {
                "title": "F1",
                "description": "Harmonic mean of precision and recall",
                "suffix": "%",
                "modify": lambda x: x * 100,
                "min": 0,
                "max": 100,
                "scale": "RdYlGn",
            },
        }
        if successful:
            self.general_stats_addcols(successful, metric_headers)

        table_headers = {
            "query": {
                "title": "Query",
                "description": "Named DayOA callset benchmarked by Truvari",
            },
            "status": {
                "title": "Status",
                "description": "Terminal diagnostic status",
            },
            "TP-base": {
                "title": "TP truth",
                "description": "Truth records matched by the query",
                "format": "{:,.0f}",
                "scale": "Greens",
            },
            "TP-comp": {
                "title": "TP query",
                "description": "Query records matched to truth",
                "format": "{:,.0f}",
                "scale": "Greens",
            },
            "FP": {
                "title": "FP",
                "description": "Query records not matched to truth",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            "FN": {
                "title": "FN",
                "description": "Truth records not matched by the query",
                "format": "{:,.0f}",
                "scale": "Reds",
            },
            **metric_headers,
            "projected_records": {
                "title": "Benchmarked",
                "description": "DEL/INS records at least 50 bp within the truth BED",
                "format": "{:,.0f}",
                "scale": "Blues",
            },
            "excluded_records": {
                "title": "Excluded",
                "description": "Records retained in source data but excluded from this projection",
                "format": "{:,.0f}",
                "scale": "Oranges",
            },
        }
        alerts = []
        if failed:
            failed_queries = ", ".join(sorted(str(row["query"]) for row in failed.values()))
            alerts.append(
                SectionAlert(
                    message=(
                        "Diagnostic failures were retained for: "
                        f"{failed_queries}. See terminal receipts and logs for evidence."
                    ),
                    level="warning",
                )
            )
        self.add_section(
            name="DayOA named-query concordance",
            anchor="truvari-dayoa-named-query-concordance",
            description=(
                "Terminal Truvari results for the complete DayOA HG002 query matrix. "
                "Diagnostic failures do not imply a release failure."
            ),
            alerts=alerts,
            plot=table.plot(
                data=data,
                headers=table_headers,
                pconfig={
                    "id": "truvari-dayoa-named-query-table",
                    "title": "Truvari: DayOA named-query concordance",
                },
            ),
        )

        if successful:
            scatter_data = {
                sample: {
                    "x": row["precision"] * 100,
                    "y": row["recall"] * 100,
                }
                for sample, row in successful.items()
                if row["precision"] is not None and row["recall"] is not None
            }
            if scatter_data:
                self.add_section(
                    name="DayOA precision vs. recall",
                    anchor="truvari-dayoa-precision-recall",
                    description=(
                        "Precision and recall for successful named-query diagnostics against GIAB GRCh38 SV truth."
                    ),
                    plot=scatter.plot(
                        scatter_data,
                        {
                            "id": "truvari-dayoa-precision-recall-plot",
                            "title": "Truvari: DayOA precision vs. recall",
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

        self._dayoa_data = data
        return len(data)
