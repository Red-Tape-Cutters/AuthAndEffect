"""Validator: data-quality rules for long-format PA metrics.

Rules return *issues* rather than raising, so a whole file can be checked at once and
problem rows can be flagged instead of silently dropped. Severity is ``"error"`` for
values that cannot be right and ``"warning"`` for values that are legal but suspicious.
"""

from __future__ import annotations

import pandas as pd

from authandeffect.schema import (
    ENTITY_LEVELS,
    KEY_COLUMNS,
    METRICS,
    PCT_METRICS,
    REQUEST_TYPES,
    REQUIRED_COLUMNS,
    SEGMENTS,
    TIME_METRICS,
)

ISSUE_COLUMNS = ["row", "rule", "severity", "message"]


class SchemaError(ValueError):
    """Raised when a table is missing columns required by the target schema."""


def _issue(row, rule: str, severity: str, message: str) -> dict:
    return {"row": row, "rule": rule, "severity": severity, "message": message}


def _check_required(df: pd.DataFrame) -> list[dict]:
    issues = []
    for col in REQUIRED_COLUMNS:
        blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        for idx in df.index[blank]:
            issues.append(_issue(idx, "required_value", "error", f"{col} is empty"))
    return issues


def _check_enums(df: pd.DataFrame) -> list[dict]:
    allowed = {
        "segment": SEGMENTS,
        "entity_level": ENTITY_LEVELS,
        "request_type": REQUEST_TYPES,
        "metric": METRICS,
    }
    issues = []
    for col, values in allowed.items():
        bad = ~df[col].isin(values)
        for idx in df.index[bad]:
            issues.append(_issue(idx, "enum", "error", f"{col}={df.at[idx, col]!r} not allowed"))
    return issues


def _check_units(df: pd.DataFrame) -> list[dict]:
    issues = []
    pct_bad = df["metric"].isin(PCT_METRICS) & (df["unit"] != "pct")
    time_bad = df["metric"].isin(TIME_METRICS) & ~df["unit"].isin(["days", "hours"])
    for idx in df.index[pct_bad | time_bad]:
        msg = f"unit {df.at[idx, 'unit']!r} does not fit metric {df.at[idx, 'metric']!r}"
        issues.append(_issue(idx, "unit_mismatch", "error", msg))
    return issues


def _check_ranges(df: pd.DataFrame) -> list[dict]:
    issues = []
    pct = df["metric"].isin(PCT_METRICS)
    out_of_range = pct & ((df["value"] < 0) | (df["value"] > 100))
    for idx in df.index[out_of_range]:
        msg = f"percentage {df.at[idx, 'value']} outside [0, 100]"
        issues.append(_issue(idx, "pct_range", "error", msg))
    negative_time = df["metric"].isin(TIME_METRICS) & (df["value"] < 0)
    for idx in df.index[negative_time]:
        issues.append(_issue(idx, "negative_time", "error", "decision time is negative"))
    return issues


def _check_counts(df: pd.DataFrame, pct_tolerance: float) -> list[dict]:
    """Percentages must agree with count / denominator when both are reported."""
    issues = []
    has_counts = df["metric"].isin(PCT_METRICS) & df["count"].notna() & df["denominator"].notna()
    for idx in df.index[has_counts]:
        count, denom, value = df.at[idx, "count"], df.at[idx, "denominator"], df.at[idx, "value"]
        if count > denom:
            msg = f"count {count} exceeds denominator {denom}"
            issues.append(_issue(idx, "count_exceeds_denominator", "error", msg))
        elif denom == 0:
            msg = "denominator is 0; percentage carries no information"
            issues.append(_issue(idx, "zero_denominator", "warning", msg))
            if value != 0:
                msg = f"denominator is 0 but value is {value}"
                issues.append(_issue(idx, "pct_matches_counts", "error", msg))
        else:
            implied = 100.0 * float(count) / float(denom)
            if abs(implied - value) > pct_tolerance:
                msg = f"reported {value} but count/denominator gives {implied:.3f}"
                issues.append(_issue(idx, "pct_matches_counts", "error", msg))
    return issues


def _check_approve_deny_sum(df: pd.DataFrame, sum_tolerance: float) -> list[dict]:
    """Approved + denied should be about 100% for each entity and request type."""
    issues = []
    group_cols = [c for c in KEY_COLUMNS if c != "metric"]
    subset = df[df["metric"].isin(["approved", "denied"])]
    for _, group in subset.groupby(group_cols, dropna=False):
        if set(group["metric"]) != {"approved", "denied"}:
            continue
        total = group["value"].sum()
        if abs(total - 100.0) > sum_tolerance:
            for idx in group.index:
                msg = f"approved + denied = {total:.2f}, expected 100"
                issues.append(_issue(idx, "approve_deny_sum", "warning", msg))
    return issues


def _check_duplicates(df: pd.DataFrame) -> list[dict]:
    dup = df.duplicated(subset=list(KEY_COLUMNS), keep=False)
    return [
        _issue(idx, "duplicate_key", "error", "another row has the same key")
        for idx in df.index[dup]
    ]


def validate_metrics(
    df: pd.DataFrame, pct_tolerance: float = 0.01, sum_tolerance: float = 0.05
) -> pd.DataFrame:
    """Check a long-format metrics table against the target schema rules.

    Args:
        df: Long-format metrics (for example from :func:`authandeffect.read_metrics`).
        pct_tolerance: Allowed gap, in percentage points, between a reported percentage
            and ``100 * count / denominator``. The default covers two-decimal rounding.
        sum_tolerance: Allowed gap between ``approved + denied`` and 100.

    Returns:
        A DataFrame with columns ``row, rule, severity, message``; empty when clean.

    Raises:
        SchemaError: If required columns are missing entirely.
    """
    needed = set(REQUIRED_COLUMNS) | set(KEY_COLUMNS) | {"count", "denominator"}
    missing = sorted(needed - set(df.columns))
    if missing:
        raise SchemaError(f"missing required columns: {missing}")

    issues: list[dict] = []
    issues += _check_required(df)
    issues += _check_enums(df)
    issues += _check_units(df)
    issues += _check_ranges(df)
    issues += _check_counts(df, pct_tolerance)
    issues += _check_approve_deny_sum(df, sum_tolerance)
    issues += _check_duplicates(df)
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def is_valid(issues: pd.DataFrame) -> bool:
    """Return True when an issue table contains no errors (warnings are allowed).

    Args:
        issues: Output of :func:`validate_metrics`.

    Returns:
        Whether the checked table is free of errors.
    """
    return not (issues["severity"] == "error").any()
