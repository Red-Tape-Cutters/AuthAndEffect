"""Tests for data-quality rules in authandeffect.validate."""

import pandas as pd
import pytest

from authandeffect import SchemaError, is_valid, validate_metrics


def rules(issues: pd.DataFrame, severity: str | None = None) -> set:
    """Return the set of rule names in an issue table, optionally for one severity."""
    if severity:
        issues = issues[issues["severity"] == severity]
    return set(issues["rule"])


def test_seed_data_has_no_errors(seed):
    """The bundled seed data passes all error-level rules."""
    issues = validate_metrics(seed)
    assert is_valid(issues), issues.to_string()


def test_seed_zero_denominators_are_warnings(seed):
    """'0 out of 0' extension metrics are flagged as warnings, not errors."""
    issues = validate_metrics(seed)
    assert rules(issues) == {"zero_denominator"}
    assert set(issues["severity"]) == {"warning"}


def test_minimal_table_is_clean(minimal):
    """A small consistent table produces no issues at all."""
    assert validate_metrics(minimal).empty


def test_missing_column_raises(minimal):
    """Dropping a required column is a schema error, not an issue row."""
    with pytest.raises(SchemaError, match="value"):
        validate_metrics(minimal.drop(columns=["value"]))


def test_percentage_out_of_range(minimal):
    """Percentages above 100 are errors."""
    minimal.loc[0, "value"] = 101.0
    assert "pct_range" in rules(validate_metrics(minimal), "error")


def test_percentage_disagrees_with_counts(minimal):
    """A percentage that does not match count/denominator is an error."""
    minimal.loc[0, "value"] = 85.0
    minimal.loc[1, "value"] = 15.0
    assert "pct_matches_counts" in rules(validate_metrics(minimal), "error")


def test_count_exceeds_denominator(minimal):
    """A count larger than its denominator is an error."""
    minimal.loc[0, "count"] = 150
    assert "count_exceeds_denominator" in rules(validate_metrics(minimal), "error")


def test_zero_denominator_with_nonzero_value(minimal):
    """0 out of 0 must be reported as 0%."""
    minimal.loc[0, ["count", "denominator", "value"]] = [0, 0, 5.0]
    issues = validate_metrics(minimal)
    assert "pct_matches_counts" in rules(issues, "error")
    assert "zero_denominator" in rules(issues, "warning")


def test_approve_deny_sum_warning(minimal):
    """Approved plus denied far from 100 is flagged."""
    minimal[["count", "denominator"]] = pd.NA
    minimal.loc[0, "value"] = 80.0
    assert "approve_deny_sum" in rules(validate_metrics(minimal), "warning")


def test_negative_time(minimal):
    """Decision times cannot be negative."""
    minimal.loc[2, "value"] = -1.0
    assert "negative_time" in rules(validate_metrics(minimal), "error")


@pytest.mark.parametrize(
    ("column", "bad"),
    [("segment", "employer"), ("metric", "approval_rate"), ("request_type", "urgent")],
)
def test_enum_values(minimal, column, bad):
    """Values outside the controlled vocabularies are errors."""
    minimal.loc[0, column] = bad
    assert "enum" in rules(validate_metrics(minimal), "error")


def test_unit_mismatch(minimal):
    """A percentage metric must use unit 'pct', a time metric 'days' or 'hours'."""
    minimal.loc[0, "unit"] = "days"
    minimal.loc[2, "unit"] = "pct"
    issues = validate_metrics(minimal)
    assert (issues["rule"] == "unit_mismatch").sum() == 2


def test_required_value_blank(minimal):
    """Blank required text fields are errors."""
    minimal.loc[0, "source_url"] = ""
    assert "required_value" in rules(validate_metrics(minimal), "error")


def test_duplicate_key(minimal):
    """Two rows with the same key are both flagged."""
    doubled = pd.concat([minimal, minimal.iloc[[0]]], ignore_index=True)
    issues = validate_metrics(doubled)
    assert (issues["rule"] == "duplicate_key").sum() == 2


def test_is_valid_ignores_warnings():
    """is_valid only fails on errors."""
    warnings_only = pd.DataFrame(
        [{"row": 0, "rule": "zero_denominator", "severity": "warning", "message": ""}]
    )
    assert is_valid(warnings_only)
    assert not is_valid(warnings_only.assign(severity="error"))
