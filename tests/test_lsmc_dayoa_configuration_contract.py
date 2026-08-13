from multiqc import BaseMultiqcModule, config, report
from multiqc.core.order_modules_and_sections import order_modules_and_sections
from multiqc.plots import table
from multiqc.types import Anchor


def test_higher_section_order_weight_renders_first():
    read_qc = BaseMultiqcModule(name="Read QC", anchor=Anchor("dayoa_sequencer_reads_qc"))
    delivery = BaseMultiqcModule(name="Delivery", anchor=Anchor("dayoa_pipeline_delivery"))
    report.modules = [delivery, read_qc]
    config.skip_versions_section = True
    config.report_section_order = {
        Anchor("dayoa_sequencer_reads_qc"): {"order": 7000},
        Anchor("dayoa_pipeline_delivery"): {"order": 2000},
    }

    order_modules_and_sections()

    assert [module.anchor for module in report.modules] == [
        "dayoa_sequencer_reads_qc",
        "dayoa_pipeline_delivery",
    ]


def test_table_id_config_hides_and_moves_provenance_columns():
    config.table_columns_visible = {
        "dayoa_delivery": {
            "status": True,
            "source_path": False,
        }
    }
    config.table_columns_placement = {
        "dayoa_delivery": {
            "status": 100,
            "source_path": 9000,
        }
    }
    plot = table.plot(
        data={
            "analysis-unit-1": {
                "status": "ready",
                "metric": 42,
                "source_path": "/not/exported/in-static-test/data.tsv",
            }
        },
        headers={
            "status": {"title": "Status"},
            "metric": {"title": "Metric"},
            "source_path": {"title": "Source path"},
        },
        pconfig=table.TableConfig(id="dayoa_delivery", title="DayOA delivery"),
    )
    assert plot is not None and not isinstance(plot, str)

    columns = {
        str(column.clean_rid): column
        for section in plot.datasets[0].dt.section_by_id.values()
        for column in section.column_by_key.values()
    }

    assert columns["status"].hidden is False
    assert columns["status"].placement == 100
    assert columns["source_path"].hidden is True
    assert columns["source_path"].placement == 9000
