"""Summarisers for self-describing metadata formats the supplementary URLs use.

The tool wrappers (fetch + call) are provided. The pure functions that do the
summarising are LEARNER TODOs (G3). The data-package summary is not graded in this version. They are pure so you can test them offline
against tests/fixtures/ without network or LLM.
"""
from __future__ import annotations

import math
import re

from .base import NotImplementedTool, ToolContext, tool

LARGE_RESOURCE_BYTES = 100_000_000


# ---------------------------------------------------------------------------
# Not graded in this version (former G2). Left as a stub: no graded link uses a data package.
# ---------------------------------------------------------------------------
# Spec: https://specs.frictionlessdata.io/data-package/
# Return a dict with EXACTLY these keys (tests/test_learner_gaps.py checks them):
#   title, version, profile          : str | None, copied from the package
#   declared_licences                : the package's "licenses" list, or None if absent/empty
#   temporal                         : {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} from package["temporal"], or None
#   resources                        : [{"name", "path", "format", "bytes", "field_count"}] one per resource
#   total_bytes                      : sum of resource bytes (missing bytes count as 0)
#   largest_resource_bytes           : max resource bytes
#   matching_fields                  : fields whose name starts with any prefix in field_filter (all resources,
#                                      de-duplicated by name, max 60): [{"resource", "name", "unit", "source"}]
#                                      where "source" is field["source"]["name"] if present. [] if field_filter is None.
#   upstream_sources                 : sorted distinct field["source"]["name"] values across ALL fields
#   warnings                         : list containing (when they apply)
#                                        "NO_PACKAGE_LICENCE"         no package-level licence declared
#                                        "LARGE_RESOURCE"             any resource > LARGE_RESOURCE_BYTES
#                                        "MULTIPLE_UPSTREAM_SOURCES"  more than one upstream source
def datapackage_summary(package: dict, field_filter: list[str] | None = None) -> dict:
    raise NotImplementedTool("datapackage_summary is not implemented in this version (former G2).")


# ---------------------------------------------------------------------------
# G3: JSON-stat 2.0 dataset -> summary
# ---------------------------------------------------------------------------
# Spec: https://json-stat.org/full/
# Return a dict with EXACTLY these keys:
#   label, updated, source           : copied from the dataset
#   dimensions                       : [{"id", "size", "labels"}] in the order of dataset["id"];
#                                      labels = first 10 "code: label" strings for that dimension
#   time                             : {"first", "last", "values"} for "time" dimension, or None
#   geo_codes                        : list of codes in "geo" dimension, in index order ([] if none)
#   expected_cells                   : product of dataset["size"]
#   value_count                      : number of non-null values
#   missing_cells                    : expected_cells - value_count
#   status_counts                    : {status_code: count} from dataset.get("status"), {} if absent
#   warnings                         : ["MISSING_CELLS"] and/or ["NON_ISO_GEO_CODES"] when they apply


def _dim_codes(dim: dict) -> list[str]:
    """Extract codes from a dimension's category index (list-form or dict-form)."""
    cat = dim.get("category", {})
    idx = cat.get("index")
    if idx is None:
        return []
    if isinstance(idx, list):
        return list(idx)
    # dict-form: keys are codes, values are positions
    # Sort by position to get the canonical order
    codes = [code for code, _ in sorted(idx.items(), key=lambda kv: kv[1])]
    return codes


def _first_10_labels(dim: dict, codes: list[str]) -> list[str]:
    """Build up to 10 'code: label' strings for a dimension."""
    cat = dim.get("category", {})
    labels = cat.get("label", {})
    result = []
    for code in codes[:10]:
        lbl = labels.get(code, code)
        result.append(f"{code}: {lbl}")
    return result


def _value_count(values) -> int:
    """Count non-null values in either dict-form or list-form values."""
    if isinstance(values, list):
        return sum(1 for v in values if v is not None)
    if isinstance(values, dict):
        return sum(1 for v in values.values() if v is not None)
    return 0


def _status_counts(status) -> dict[str, int]:
    """Count status flags from dict-form or list-form status."""
    if not status:
        return {}
    counts: dict[str, int] = {}
    if isinstance(status, list):
        for s in status:
            if s is not None:
                counts[s] = counts.get(s, 0) + 1
    elif isinstance(status, dict):
        for s in status.values():
            if s is not None:
                counts[s] = counts.get(s, 0) + 1
    return counts


# ISO 3166-1 alpha-2 pattern: exactly 2 uppercase letters.
# Eurostat uses "UK" (ISO: GB) and "EL" (ISO: GR), and aggregates like "EU27_2020".
_ISO_ALPHA2_RE = re.compile(r"^[A-Z]{2}$")
# Explicit non-ISO codes that happen to match ^[A-Z]{2}$ but are not valid ISO codes.
_NON_ISO_EXPLICIT = frozenset({"UK", "EL"})


def _is_non_iso_geo(code: str) -> bool:
    """Return True if a geo code is NOT ISO 3166-1 alpha-2.

    Eurostat's "UK" (ISO: GB) and "EL" (ISO: GR) are non-ISO codes,
    as are aggregates like "EU27_2020".
    """
    if code in _NON_ISO_EXPLICIT:
        return True
    return not bool(_ISO_ALPHA2_RE.match(code))


def jsonstat_summary(dataset: dict) -> dict:
    """Summarise a JSON-stat 2.0 dataset."""
    dims_list = dataset.get("id", [])
    sizes = dataset.get("size", [])

    # Dimensions metadata
    dimensions = []
    time_info = None
    geo_codes = []
    all_geo_codes = []

    for i, dim_id in enumerate(dims_list):
        dim = dataset.get("dimension", {}).get(dim_id, {})
        codes = _dim_codes(dim)
        labels = _first_10_labels(dim, codes)
        sz = sizes[i] if i < len(sizes) else len(codes)
        dimensions.append({"id": dim_id, "size": sz, "labels": labels})

        if dim_id == "time":
            sorted_codes = sorted(codes) if codes else []
            time_info = {
                "first": sorted_codes[0] if sorted_codes else None,
                "last": sorted_codes[-1] if sorted_codes else None,
                "values": sorted_codes,
            }

        if dim_id == "geo":
            geo_codes = list(codes)
            all_geo_codes = list(codes)

    # Value counts
    values = dataset.get("value", [])
    expected_cells = math.prod(sizes) if sizes else 0
    val_count = _value_count(values)
    missing = expected_cells - val_count

    # Status
    status = dataset.get("status")
    stat_counts = _status_counts(status)

    # Warnings
    warnings = []
    if missing > 0:
        warnings.append("MISSING_CELLS")
    if all_geo_codes:
        non_iso = any(_is_non_iso_geo(c) for c in all_geo_codes)
        if non_iso:
            warnings.append("NON_ISO_GEO_CODES")

    return {
        "label": dataset.get("label"),
        "updated": dataset.get("updated"),
        "source": dataset.get("source"),
        "dimensions": dimensions,
        "time": time_info,
        "geo_codes": geo_codes,
        "expected_cells": expected_cells,
        "value_count": val_count,
        "missing_cells": missing,
        "status_counts": stat_counts,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Tool wrappers (provided)
# ---------------------------------------------------------------------------
@tool("summarize_datapackage",
      "Summarise a Frictionless Data Package descriptor (datapackage.json): licence declarations, temporal coverage, "
      "resource sizes, matching fields and their upstream sources. Reads only the descriptor, never the data files.",
      {"url": {"type": "string"},
       "field_filter": {"type": "array", "items": {"type": "string"},
                        "description": "Field-name prefixes to list, e.g. ['AB_', 'CD_load']"}},
      ["url"])
def summarize_datapackage(ctx: ToolContext, args: dict) -> dict:
    package, res = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], "last_modified_header": res.headers.get("last-modified"),
            **datapackage_summary(package, args.get("field_filter"))}


@tool("summarize_jsonstat",
      "Summarise a JSON-stat 2.0 dataset (for example from the Eurostat dissemination API): dimensions, time coverage, "
      "geo codes, missing cells and status flags.",
      {"url": {"type": "string"}}, ["url"])
def summarize_jsonstat(ctx: ToolContext, args: dict) -> dict:
    dataset, _ = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], **jsonstat_summary(dataset)}
