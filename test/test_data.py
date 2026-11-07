"""Tests for loading and reshaping metrics in authandeffect.data."""

import pandas as pd
import pytest

from authandeffect import denial_rates, load_seed, read_metrics, to_wide
from authandeffect.schema import COLUMNS, METRICS


def test_seed_shape_and_columns(seed):
    """The seed covers five real reporting entities and follows the schema column order."""
    assert list(seed.columns) == list(COLUMNS)
    assert set(seed["entity_id"]) == {"H0029", "H1468", "H5050", "H8849", "G0606"}
    assert set(seed["segment"]) == {"medicare_advantage", "medicaid_mco"}
    assert set(seed["metric"]) <= set(METRICS)


def test_seed_types(seed):
    """Counts are nullable integers, values are floats, blank text is ''."""
    assert str(seed["count"].dtype) == "Int64"
    assert pd.api.types.is_float_dtype(seed["value"])
    assert seed["state"].isna().sum() == 0
    assert (seed.loc[seed["entity_id"] == "H5050", "state"] == "WA").all()


def test_read_metrics_roundtrip(tmp_path, seed):
    """Writing then reading a metrics file keeps the data unchanged."""
    path = tmp_path / "metrics.csv"
    seed.to_csv(path, index=False)
    again = read_metrics(path)
    pd.testing.assert_frame_equal(seed, again)


def test_to_wide_one_row_per_entity_and_request_type(seed):
    """Standard + expedited per entity; an extra 'all' row where the source does not split."""
    wide = to_wide(seed)
    counts = wide.groupby("entity_id").size().to_dict()
    assert counts == {"H0029": 2, "H1468": 3, "H5050": 2, "H8849": 3, "G0606": 3}


def test_to_wide_converts_times_to_hours(seed):
    """Days are converted, so every payer's decision time is comparable."""
    wide = to_wide(seed).set_index(["entity_id", "request_type"])
    assert wide.loc[("H0029", "standard"), "mean_decision_time_hours"] == pytest.approx(120)
    assert wide.loc[("H5050", "standard"), "mean_decision_time_hours"] == pytest.approx(24)
    assert wide.loc[("H1468", "expedited"), "mean_decision_time_hours"] == pytest.approx(9)
    assert wide.loc[("H1468", "standard"), "denied_pct"] == pytest.approx(7.83)


def test_denial_rates_sorted(seed):
    """Denial rates come back highest first; volumes are missing where not published."""
    rates = denial_rates(seed, "standard")
    assert list(rates["entity_id"]) == ["H0029", "H1468", "H8849", "H5050", "G0606"]
    assert rates["denied_pct"].is_monotonic_decreasing
    assert rates.loc[0, "requests"] == 26108
    assert rates.set_index("entity_id")["requests"].isna().loc[["H8849", "G0606"]].all()


def test_denial_rates_expedited(seed):
    """Expedited rates are selected separately from standard ones."""
    rates = denial_rates(seed, "expedited")
    assert rates.set_index("entity_id").loc["H5050", "denied_pct"] == pytest.approx(8.54)


def test_load_seed_returns_new_object():
    """Each call returns an independent DataFrame."""
    first, second = load_seed(), load_seed()
    first.loc[0, "value"] = -1
    assert second.loc[0, "value"] != -1
