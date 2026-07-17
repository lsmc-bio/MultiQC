import logging
import os
from typing import Dict, List, Mapping, Union

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import bargraph, table
from multiqc.plots.table_object import ColumnDict

from .parser import parse_sample_first_tsv

log = logging.getLogger(__name__)

Value = Union[int, float, str, bool, None]
GeneralStatValue = Union[int, float, str, bool]

SECTION_NAMES = {
    "inventory": "Ultima Run Inventory",
    "demux": "Ultima Demux / Barcode Summary",
    "trimmer_stats": "Ultima Trimmer Stats",
    "trimmer_failures": "Ultima Trimmer Failure Codes",
    "flowq": "Ultima FlowQ Summary",
    "snvq": "Ultima SNVQ Summary",
    "coverage": "Ultima Coverage Summary",
    "picard": "Ultima Picard / Basic Run Metrics",
    "contamination": "Ultima Contamination / Sample Swap",
    "upload": "Ultima Upload Status",
    "unmatched": "Ultima Unmatched Outputs",
}


class MultiqcModule(BaseMultiqcModule):
    """
    Parses normalized Ultima run-QC tables produced by the open-source ur-qc package.

    The module expects small TSV summary files, typically named `ultima_*_mqc.tsv`.
    All parsed TSVs must have `Sample` as the first column. The module does not
    scan CRAM, BAM, or large bedGraph files.
    """

    def __init__(self):
        super().__init__(
            name="Ultima Run QC",
            anchor="ultima",
            href="https://github.com/lsmc-bio/ur-qc",
            info="Summarizes Ultima run-level inventory, demultiplexing, trimming, quality, coverage, and contamination evidence.",
            doi=None,
        )

        self.section_rows: Dict[str, Dict[str, Dict[str, Value]]] = {}
        self.input_provenance: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
        for section in SECTION_NAMES:
            rows = self._collect_section(section)
            if rows:
                self.section_rows[section] = rows

        self.section_rows = {
            section: filtered for section, rows in self.section_rows.items() if (filtered := self.ignore_samples(rows))
        }
        if not self.section_rows:
            raise ModuleNoSamplesFound

        log.info(f"Found {sum(len(rows) for rows in self.section_rows.values())} Ultima run-QC rows")
        self.add_software_version(None)
        self._add_general_stats()
        self._add_sections()
        self.write_data_file(self.section_rows, "multiqc_ultima")
        self.write_data_file(self.input_provenance, "multiqc_ultima_input_provenance")

    def _collect_section(self, section: str) -> Dict[str, Dict[str, Value]]:
        rows: Dict[str, Dict[str, Value]] = {}
        sources: Dict[str, List[str]] = {}
        for f in self.find_log_files(f"ultima/{section}"):
            parsed_rows = parse_sample_first_tsv(f["f"], f["fn"])
            for sample, row in parsed_rows.items():
                source = source_path(f)
                if sample in rows and rows[sample] != row:
                    paths = sorted([*sources[sample], source])
                    raise ValueError(f"Conflicting Ultima {section} inputs for sample '{sample}': {', '.join(paths)}")
                rows.setdefault(sample, dict(row))
                sources.setdefault(sample, []).append(source)
                if len(sources[sample]) == 1:
                    self.add_data_source(f, sample, section=section)
        self.input_provenance[section] = {
            sample: {"source_paths": sorted(sample_sources)} for sample, sample_sources in sources.items()
        }
        return rows

    def _add_general_stats(self) -> None:
        demux = self.section_rows.get("demux", {})
        coverage = self.section_rows.get("coverage", {})
        contamination = self.section_rows.get("contamination", {})

        gs: Dict[str, Dict[str, GeneralStatValue]] = {}
        for sample, row in demux.items():
            gs.setdefault(sample, {})
            for key in ("observed_outputs", "missing_required_outputs", "matched_reads", "failed_reads"):
                if key in row:
                    value = to_number(row[key])
                    if value is not None:
                        gs[sample][key] = value
        for sample, row in coverage.items():
            gs.setdefault(sample, {})
            for key in ("mean_depth", "median_depth", "pct_ge_30x", "pct_ge_50x"):
                if key in row:
                    value = to_number(row[key])
                    if value is not None:
                        gs[sample][key] = value
        for sample, row in contamination.items():
            gs.setdefault(sample, {})
            for key in ("FREEMIX", "PCT_contamination", "contamination_fraction"):
                if key in row:
                    value = to_number(row[key])
                    if value is not None:
                        gs[sample][key] = value

        if not gs:
            return

        headers: Dict[str, ColumnDict] = {
            "observed_outputs": {
                "title": "Ultima Observed Outputs",
                "description": "Observed required and optional output files",
            },
            "missing_required_outputs": {
                "title": "Ultima Missing Required",
                "description": "Required Ultima output files missing from run evidence",
            },
            "matched_reads": {
                "title": "Ultima Matched Reads",
                "description": "Matched or demultiplexed reads when reported",
            },
            "failed_reads": {"title": "Ultima Failed Reads", "description": "Failed reads when reported"},
            "mean_depth": {
                "title": "Ultima Mean Depth",
                "suffix": "x",
                "description": "Mean depth from normalized Ultima coverage outputs",
            },
            "median_depth": {
                "title": "Ultima Median Depth",
                "suffix": "x",
                "description": "Median depth from normalized Ultima coverage outputs",
            },
            "pct_ge_30x": {"title": "Ultima >=30x", "suffix": "%", "description": "Percent of bases at or above 30x"},
            "pct_ge_50x": {"title": "Ultima >=50x", "suffix": "%", "description": "Percent of bases at or above 50x"},
            "FREEMIX": {"title": "Ultima FREEMIX", "description": "FREEMIX from selfSM output"},
            "PCT_contamination": {
                "title": "Ultima Contam %",
                "suffix": "%",
                "description": "Percent contamination from selfSM contamination stats",
            },
            "contamination_fraction": {
                "title": "Ultima Contam Frac",
                "description": "Contamination fraction from normalized output",
            },
        }
        self.general_stats_addcols(gs, headers)

    def _add_sections(self) -> None:
        for section, rows in self.section_rows.items():
            if section in {"demux", "trimmer_failures", "coverage"}:
                plot = self._section_bargraph(section, rows)
            else:
                plot = self._section_table(section, rows)
            self.add_section(
                name=SECTION_NAMES[section],
                anchor=f"ultima-{section}",
                description=section_description(section),
                plot=plot,
            )

    def _section_table(self, section: str, rows: Mapping[str, Mapping[str, Value]]):
        headers = table_headers(rows)
        return table.plot(rows, headers, {"id": f"ultima_{section}", "title": SECTION_NAMES[section]})

    def _section_bargraph(self, section: str, rows: Mapping[str, Mapping[str, Value]]):
        keys = bargraph_keys(section, rows)
        if not keys:
            return self._section_table(section, rows)
        data = {sample: {key: to_number(row[key]) for key in keys if key in row} for sample, row in rows.items()}
        cats = {key: {"name": pretty_name(key)} for key in keys}
        return bargraph.plot(data, cats, {"id": f"ultima_{section}_bar", "title": SECTION_NAMES[section]})


def table_headers(rows: Mapping[str, Mapping[str, Value]]) -> Dict[str, ColumnDict]:
    headers: Dict[str, ColumnDict] = {}
    for row in rows.values():
        for key in row:
            headers.setdefault(key, {"title": pretty_name(key)})
    return headers


def source_path(file_obj: Mapping[str, object]) -> str:
    return os.path.join(str(file_obj.get("root", "")), str(file_obj.get("fn", "")))


def bargraph_keys(section: str, rows: Mapping[str, Mapping[str, Value]]) -> List[str]:
    preferred = {
        "demux": ["expected_outputs", "observed_outputs", "missing_required_outputs"],
        "trimmer_failures": ["failed_read_count", "total_read_count"],
        "coverage": ["pct_ge_1x", "pct_ge_10x", "pct_ge_20x", "pct_ge_30x", "pct_ge_50x"],
    }[section]
    available = set().union(*(row.keys() for row in rows.values())) if rows else set()
    return [key for key in preferred if key in available]


def to_number(value: Value) -> Value:
    if value in {"", None}:
        return value
    text = str(value)
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return value


def pretty_name(value: str) -> str:
    return value.replace("_", " ").replace(">=", "At least ").title()


def section_description(section: str) -> str:
    if section == "flowq":
        return "Native Ultima FlowQ summary. FlowQ is not treated as an Illumina-equivalent Q-score."
    if section == "snvq":
        return "Native Ultima SNVQ summary. SNVQ is not treated as an Illumina-equivalent Q-score."
    return SECTION_NAMES[section]
