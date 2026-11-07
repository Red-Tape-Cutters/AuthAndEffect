"""Shared pytest fixtures."""

import pandas as pd
import pytest

from authandeffect import load_seed


@pytest.fixture
def seed() -> pd.DataFrame:
    """Return a fresh copy of the bundled seed dataset."""
    return load_seed()


@pytest.fixture
def minimal() -> pd.DataFrame:
    """Return a small, valid long-format table for one fictional contract."""
    base = {
        "reporting_year": 2025,
        "parent_org": "Example Parent",
        "brand": "Example Plan",
        "segment": "medicare_advantage",
        "entity_level": "contract",
        "entity_id": "H0000",
        "state": "",
        "source_id": "example-ma",
        "source_url": "https://example.org/report.pdf",
        "retrieved_on": "2026-10-30",
        "reported_text": "",
        "notes": "",
    }
    rows = [
        {"request_type": "standard", "metric": "approved", "count": 90, "denominator": 100,
         "value": 90.0, "unit": "pct"},
        {"request_type": "standard", "metric": "denied", "count": 10, "denominator": 100,
         "value": 10.0, "unit": "pct"},
        {"request_type": "standard", "metric": "mean_decision_time", "count": pd.NA,
         "denominator": pd.NA, "value": 2.0, "unit": "days"},
    ]  # fmt: skip
    df = pd.DataFrame([{**base, **r} for r in rows])
    df["count"] = df["count"].astype("Int64")
    df["denominator"] = df["denominator"].astype("Int64")
    return df
