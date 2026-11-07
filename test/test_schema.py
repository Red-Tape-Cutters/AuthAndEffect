"""Tests for unit conversion and duration parsing in authandeffect.schema."""

import math

import pytest

from authandeffect.schema import (
    COLUMNS,
    KEY_COLUMNS,
    METRICS,
    REQUIRED_COLUMNS,
    parse_duration,
    to_hours,
)


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [(1, "days", 24.0), (0.5, "days", 12.0), (9, "hours", 9.0), (0, "hours", 0.0)],
)
def test_to_hours_converts(value, unit, expected):
    """Days are multiplied by 24 and hours pass through."""
    assert to_hours(value, unit) == expected


@pytest.mark.parametrize("bad_unit", ["pct", "minutes", ""])
def test_to_hours_rejects_unknown_unit(bad_unit):
    """Only days and hours are time units."""
    with pytest.raises(ValueError, match="unit"):
        to_hours(1, bad_unit)


@pytest.mark.parametrize("bad_value", [-1, math.nan])
def test_to_hours_rejects_negative_or_nan(bad_value):
    """Durations cannot be negative or missing."""
    with pytest.raises(ValueError, match="non-negative"):
        to_hours(bad_value, "hours")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1 Days 0 Hours", 24.0),  # Kaiser
        ("0 Days 4 Hours", 4.0),  # Kaiser
        ("9 hour(s)", 9.0),  # Humana
        ("1 day(s)", 24.0),  # Humana
        ("5 days", 120.0),  # Wellcare
        ("26 hrs", 26.0),
        ("1.5 days", 36.0),
        ("2 DAYS 3 HOURS", 51.0),
    ],
)
def test_parse_duration_formats_seen_in_reports(text, expected):
    """Duration strings printed by different payers parse to the same unit."""
    assert parse_duration(text) == expected


@pytest.mark.parametrize("text", ["", "   ", None, "about a day", "N/A"])
def test_parse_duration_rejects_unparseable(text):
    """Text without a number and unit raises ValueError."""
    with pytest.raises(ValueError):
        parse_duration(text)


def test_schema_constants_are_consistent():
    """Required and key columns are part of the column list; metric names are unique."""
    assert set(REQUIRED_COLUMNS) <= set(COLUMNS)
    assert set(KEY_COLUMNS) <= set(COLUMNS)
    assert len(METRICS) == len(set(METRICS))
