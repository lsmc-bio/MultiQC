"""Render small report fixtures to verify compact-only LSMC branding."""

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup

import multiqc
from multiqc.core.update_config import ClConfig

output = ROOT / "output/playwright/lsmc-logo"
source = output / "inputs"
source.mkdir(parents=True, exist_ok=True)
(source / "metrics_mqc.tsv").write_text(
    '# plot_type: "table"\n# section_name: "Logo preview metrics"\nSample\tReads\nExample-1\t100\nExample-2\t200\n'
)
expected = "data:image/png;base64," + base64.b64encode(
    (ROOT / "multiqc/templates/default/assets/img/lsmc-compact-black-transparent.png").read_bytes()
).decode("ascii")
dark = "data:image/png;base64," + base64.b64encode(
    (ROOT / "multiqc/templates/default/assets/img/lsmc-compact-white-transparent.png").read_bytes()
).decode("ascii")
receipts = []
for template, folder in [("default", "single"), ("lsmc-paginated", "paginated")]:
    destination = output / folder
    result = multiqc.run(
        source,
        cfg=ClConfig(
            template=template,
            output_dir=str(destination),
            title="LSMC logo preview",
            no_ai=True,
            no_version_check=True,
            force=True,
        ),
    )
    assert result.sys_exit_code == 0
    pages = []
    for path in destination.rglob("*.html"):
        soup = BeautifulSoup(path.read_text(), "html.parser")
        logos = soup.select(".lsmc-native-brand img")
        if not logos:
            continue
        assert all(logo["src"] in {expected, dark} for logo in logos), str(path)
        assert soup.select_one(".theme-icon-active img")["src"] == expected
        pages.append(str(path.relative_to(ROOT)))
    assert pages
    receipts.append({"template": template, "verified_pages": pages})
print(json.dumps(receipts, indent=2))
