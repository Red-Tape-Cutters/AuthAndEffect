"""Target schema (v0.1) for standardized prior authorization metrics.

The dataset is stored in *long* (tidy) format: one row per
(reporting year, reporting entity, request type, metric). Long format lets payers that
report extra optional metrics (for example "approved within 14 days") live in the same
table as payers that report only the required ones, without empty columns.

See ``doc/schema.md`` for the full data dictionary.
"""

from __future__ import annotations

import math
import re

SCHEMA_VERSION = "0.1.0"

#: Market segments covered by CMS-0057-F.
SEGMENTS = (
    "medicare_advantage",
    "medicaid_mco",
    "chip_mco",
    "medicaid_ffs",
    "chip_ffs",
    "qhp_ffe",
)

#: Level at which a payer reported. CMS guidance: MA by contract, managed care by plan,
#: FFS programs by state, QHP issuers by issuer. "region" covers payers such as Kaiser
#: that publish one report per region containing several contracts.
ENTITY_LEVELS = ("contract", "plan", "state", "issuer", "region")

#: "all" is used when a payer does not split a metric by request type (appeals often).
REQUEST_TYPES = ("standard", "expedited", "all")

#: Metrics required by CMS-0057-F, expressed as percentages.
REQUIRED_PCT_METRICS = (
    "approved",
    "denied",
    "approved_after_extension",
    "approved_after_appeal",
)

#: Optional percentage metrics that some payers report.
OPTIONAL_PCT_METRICS = (
    "denied_after_extension",
    "denied_after_appeal",
    "approved_within_timeframe",
    "denied_within_timeframe",
)

PCT_METRICS = REQUIRED_PCT_METRICS + OPTIONAL_PCT_METRICS

#: Decision-time metrics (required for both standard and expedited requests).
TIME_METRICS = ("mean_decision_time", "median_decision_time")

METRICS = PCT_METRICS + TIME_METRICS

UNITS = ("pct", "days", "hours")

#: Column order of the long-format table.
COLUMNS = (
    "reporting_year",
    "parent_org",
    "brand",
    "segment",
    "entity_level",
    "entity_id",
    "state",
    "request_type",
    "metric",
    "count",
    "denominator",
    "value",
    "unit",
    "reported_text",
    "source_id",
    "source_url",
    "retrieved_on",
    "notes",
)

#: Columns that must be non-empty on every row.
REQUIRED_COLUMNS = (
    "reporting_year",
    "parent_org",
    "brand",
    "segment",
    "entity_level",
    "entity_id",
    "request_type",
    "metric",
    "value",
    "unit",
    "source_id",
    "source_url",
)

#: Columns that identify a single observation.
KEY_COLUMNS = (
    "reporting_year",
    "source_id",
    "entity_id",
    "state",
    "request_type",
    "metric",
)

_HOURS_PER_UNIT = {"hours": 1.0, "days": 24.0}

_DURATION_PART = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>days?|day\(s\)|hours?|hour\(s\)|hrs?)",
    flags=re.IGNORECASE,
)


def to_hours(value: float, unit: str) -> float:
    """Convert a duration expressed in ``days`` or ``hours`` to hours.

    Args:
        value: The numeric duration.
        unit: Either ``"days"`` or ``"hours"``.

    Returns:
        The duration in hours.

    Raises:
        ValueError: If ``unit`` is not a time unit or ``value`` is negative or NaN.
    """
    if unit not in _HOURS_PER_UNIT:
        raise ValueError(f"unit must be one of {sorted(_HOURS_PER_UNIT)}, got {unit!r}")
    value = float(value)
    if math.isnan(value) or value < 0:
        raise ValueError(f"duration must be a non-negative number, got {value!r}")
    return value * _HOURS_PER_UNIT[unit]


def parse_duration(text: str) -> float:
    """Parse a duration string as printed in payer reports into hours.

    Handles the layouts seen in the 2025 reports, for example ``"1 Days 0 Hours"``
    (Kaiser), ``"9 hour(s)"`` and ``"1 day(s)"`` (Humana), ``"5 days"`` (Wellcare)
    and ``"26"`` with an explicit default unit.

    Args:
        text: The duration as printed in the source document.

    Returns:
        The total duration in hours.

    Raises:
        ValueError: If no duration can be parsed from ``text``.
    """
    if text is None or not str(text).strip():
        raise ValueError("empty duration text")
    parts = list(_DURATION_PART.finditer(str(text)))
    if not parts:
        raise ValueError(f"could not parse a duration from {text!r}")
    total = 0.0
    for part in parts:
        unit = "days" if part.group("unit").lower().startswith("d") else "hours"
        total += to_hours(float(part.group("num")), unit)
    return total
