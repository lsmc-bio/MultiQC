"""
=========
 default
=========

The main MultiQC report template, lovingly known to its admirers
simply as "default"

Note, this is where most of the MultiQC report interactive functionality
is based and will be developed. Unless you want to do some really radical
changes, you probably don't want to replace this theme. Instead, you can
create a child theme that starts with 'default' and then overwrites
certain files.

For more information about creating child themes, see the docs:
docs/templates.md

"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


DAYOA_SELECTOR_SCHEMA_VERSION = "dayoa-report-selectors-v2"
DAYOA_SELECTOR_MODALITIES = {"sr", "lr", "hybrid", "global"}
DAYOA_SELECTOR_REQUIRED_FIELDS = {
    "MultiQCAnalysisID",
    "modality",
    "SPECIMEN_ID",
    "SPECIMEN_EUID",
    "SAMPLEID",
    "SAMPLE_EUID",
    "ANALYSIS_UNIT_UID",
    "LIBRARY_EUID",
    "LIBRARY_IDS",
    "LIBRARY_EUIDS",
    "section",
    "grain",
    "pair_endpoint_roles",
}


def load_dayoa_selector_manifest(path: str) -> Dict[str, Any]:
    """Load and validate the exact DayOA selector manifest used by the report UI."""

    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid DayOA selector JSON in {manifest_path}: {error}") from error

    if not isinstance(manifest, dict):
        raise ValueError(f"DayOA selector manifest must be a JSON object: {manifest_path}")
    if manifest.get("schema_version") != DAYOA_SELECTOR_SCHEMA_VERSION:
        raise ValueError(
            f"DayOA selector manifest schema_version must be {DAYOA_SELECTOR_SCHEMA_VERSION}: {manifest_path}"
        )

    records = manifest.get("records")
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError(f"DayOA selector manifest records must be a non-empty array: {manifest_path}")

    seen_analysis_ids: set[str] = set()
    identity_maps: Dict[str, Dict[str, Optional[str]]] = {"specimen": {}, "sample": {}, "library": {}}
    identity_reverse_maps: Dict[str, Dict[str, str]] = {"specimen": {}, "sample": {}, "library": {}}
    identity_fields = {
        "specimen": ("SPECIMEN_ID", "SPECIMEN_EUID"),
        "sample": ("SAMPLEID", "SAMPLE_EUID"),
    }

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"DayOA selector record {index} must be an object: {manifest_path}")
        missing = sorted(DAYOA_SELECTOR_REQUIRED_FIELDS - set(record))
        if missing:
            raise ValueError(
                f"DayOA selector record {index} is missing required fields {', '.join(missing)}: {manifest_path}"
            )

        analysis_id = record["MultiQCAnalysisID"]
        if not isinstance(analysis_id, str) or not analysis_id.strip():
            raise ValueError(f"DayOA selector record {index} has a blank MultiQCAnalysisID: {manifest_path}")
        if analysis_id in seen_analysis_ids:
            raise ValueError(f"Duplicate MultiQCAnalysisID '{analysis_id}' in {manifest_path}")
        seen_analysis_ids.add(analysis_id)

        modality = record["modality"]
        if modality not in DAYOA_SELECTOR_MODALITIES:
            raise ValueError(
                f"DayOA selector record {index} has invalid modality '{modality}', expected one of "
                f"{', '.join(sorted(DAYOA_SELECTOR_MODALITIES))}: {manifest_path}"
            )

        for field in ("section", "grain"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"DayOA selector record {index} has a blank {field}: {manifest_path}")
        if not isinstance(record["pair_endpoint_roles"], list) or not all(
            isinstance(role, str) and role.strip() for role in record["pair_endpoint_roles"]
        ):
            raise ValueError(
                f"DayOA selector record {index} pair_endpoint_roles must be an array of non-empty strings: "
                f"{manifest_path}"
            )

        for identity_type, (id_field, euid_field) in identity_fields.items():
            identity = record[id_field]
            euid = record[euid_field]
            if identity is None and euid is None:
                continue
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError(
                    f"DayOA selector record {index} must provide {id_field} whenever {euid_field} is present: "
                    f"{manifest_path}"
                )
            if euid is not None and (not isinstance(euid, str) or not euid.strip()):
                raise ValueError(
                    f"DayOA selector record {index} has an invalid {euid_field}; use a persisted non-empty EUID "
                    f"or JSON null, never a guessed placeholder: {manifest_path}"
                )
            previous_euid = identity_maps[identity_type].setdefault(identity, euid)
            if previous_euid != euid:
                raise ValueError(
                    f"DayOA selector record {index} has conflicting {identity_type} identity mapping: {manifest_path}"
                )
            if euid is not None:
                previous_id = identity_reverse_maps[identity_type].setdefault(euid, identity)
                if previous_id != identity:
                    raise ValueError(
                        f"DayOA selector record {index} has conflicting {identity_type} identity mapping: "
                        f"{manifest_path}"
                    )

        library_ids = record["LIBRARY_IDS"]
        library_euids = record["LIBRARY_EUIDS"]
        if not isinstance(library_ids, list) or not all(
            isinstance(library_id, str) and library_id.strip() for library_id in library_ids
        ):
            raise ValueError(
                f"DayOA selector record {index} LIBRARY_IDS must be an array of non-empty strings: "
                f"{manifest_path}"
            )
        if not isinstance(library_euids, list) or not all(
            isinstance(library_euid, str) and library_euid.strip() for library_euid in library_euids
        ):
            raise ValueError(
                f"DayOA selector record {index} LIBRARY_EUIDS must contain persisted non-empty EUIDs "
                f"or be empty, never a guessed placeholder: {manifest_path}"
            )
        if library_euids and len(library_ids) != len(library_euids):
            raise ValueError(
                f"DayOA selector record {index} must pair every LIBRARY_ID with one LIBRARY_EUID when "
                f"library EUIDs are present: {manifest_path}"
            )
        singular_library_euid = record["LIBRARY_EUID"]
        if singular_library_euid is not None and (
            not isinstance(singular_library_euid, str) or not singular_library_euid.strip()
        ):
            raise ValueError(
                f"DayOA selector record {index} has an invalid LIBRARY_EUID, never a guessed placeholder: "
                f"{manifest_path}"
            )
        expected_singular_library_euid = library_euids[0] if len(library_euids) == 1 else None
        if singular_library_euid != expected_singular_library_euid:
            raise ValueError(
                f"DayOA selector record {index} LIBRARY_EUID must equal the one physical library EUID, "
                f"or be null when zero or multiple libraries are selected: {manifest_path}"
            )
        for library_id, library_euid in zip(library_ids, library_euids):
            previous_euid = identity_maps["library"].setdefault(library_id, library_euid)
            if previous_euid != library_euid:
                raise ValueError(
                    f"DayOA selector record {index} has conflicting library identity mapping: {manifest_path}"
                )
            previous_id = identity_reverse_maps["library"].setdefault(library_euid, library_id)
            if previous_id != library_id:
                raise ValueError(
                    f"DayOA selector record {index} has conflicting library identity mapping: {manifest_path}"
                )

    return manifest


template_dir = os.path.dirname(__file__)
base_fn = "base.html"
template_functions = {"load_dayoa_selector_manifest": load_dayoa_selector_manifest}
