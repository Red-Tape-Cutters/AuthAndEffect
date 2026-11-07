"""Data manager: load standardized PA metrics and reshape them for analysis."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import pandas as pd

from authandeffect.schema import COLUMNS, TIME_METRICS, to_hours

SEED_FILE = "seed_metrics_2025.csv"

_STRING_COLUMNS = (
    "parent_org",
    "brand",
    "segment",
    "entity_level",
    "entity_id",
    "state",
    "request_type",
    "metric",
    "unit",
    "reported_text",
    "source_id",
    "source_url",
    "retrieved_on",
    "notes",
)

WIDE_INDEX = [
    "reporting_year",
    "parent_org",
    "brand",
    "segment",
    "entity_level",
    "entity_id",
    "state",
    "request_type",
]


def read_metrics(path: str | Path) -> pd.DataFrame:
    """Read a long-format metrics CSV and coerce column types.

    Empty text cells become ``""`` (not NaN) so they can be used in group keys.
    ``count`` and ``denominator`` use pandas' nullable integer type because many payers
    publish percentages only.

    Args:
        path: Path to a CSV file that follows the target schema.

    Returns:
        A DataFrame with the columns of the target schema, in schema order when present.
    """
    df = pd.read_csv(path, dtype={c: "string" for c in _STRING_COLUMNS}, keep_default_na=False)
    for col in _STRING_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    for col in ("count", "denominator"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace("", pd.NA)).astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"].replace("", pd.NA), errors="coerce")
    if "reporting_year" in df.columns:
        df["reporting_year"] = pd.to_numeric(df["reporting_year"]).astype("Int64")
    ordered = [c for c in COLUMNS if c in df.columns]
    extra = [c for c in df.columns if c not in COLUMNS]
    return df[ordered + extra]


def load_seed() -> pd.DataFrame:
    """Load the hand-entered 2025 seed dataset bundled with the package.

    Returns:
        The seed metrics in long format (see :func:`read_metrics`).
    """
    with resources.as_file(resources.files("authandeffect") / "data" / SEED_FILE) as path:
        return read_metrics(path)


def add_standard_value(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``value_std``: percentages unchanged, decision times converted to hours.

    Args:
        df: Long-format metrics.

    Returns:
        A copy of ``df`` with a ``value_std`` column.
    """
    out = df.copy()
    is_time = out["metric"].isin(TIME_METRICS)
    out["value_std"] = out["value"].astype(float)
    out.loc[is_time, "value_std"] = [
        to_hours(v, u)
        for v, u in zip(out.loc[is_time, "value"], out.loc[is_time, "unit"], strict=True)
    ]
    return out


def to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-format metrics to one row per entity and request type.

    Percentage metrics become ``<metric>_pct`` columns; decision times are converted to
    hours and become ``<metric>_hours`` columns.

    Args:
        df: Long-format metrics.

    Returns:
        A wide DataFrame indexed by a flat range index.
    """
    std = add_standard_value(df)
    suffix = std["metric"].isin(TIME_METRICS).map({True: "_hours", False: "_pct"})
    std["column"] = std["metric"] + suffix
    wide = std.pivot_table(
        index=WIDE_INDEX, columns="column", values="value_std", aggfunc="first"
    ).reset_index()
    wide.columns.name = None
    return wide


def denial_rates(df: pd.DataFrame, request_type: str = "standard") -> pd.DataFrame:
    """Return denial rates for one request type, highest first.

    Args:
        df: Long-format metrics.
        request_type: ``"standard"`` or ``"expedited"``.

    Returns:
        Columns ``parent_org, brand, entity_id, state, denied_pct, requests`` where
        ``requests`` is the denominator (total requests) when the payer reported it.
    """
    rows = df[(df["metric"] == "denied") & (df["request_type"] == request_type)]
    out = rows[["parent_org", "brand", "entity_id", "state", "value", "denominator"]].rename(
        columns={"value": "denied_pct", "denominator": "requests"}
    )
    return out.sort_values("denied_pct", ascending=False).reset_index(drop=True)
