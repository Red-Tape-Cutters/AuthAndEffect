"""Tests for the payer source registry in authandeffect.registry."""

import pytest

from authandeffect import get_source, load_reference_datasets, load_registry
from authandeffect.registry import registry_frame, validate_registry

BAD_REGISTRY = """
payer_sources:
  - id: dup
    parent_org: A
    brand: A
    segment: employer
    granularity: county
    formats: [docx]
    status: located
  - id: dup
    parent_org: B
    brand: B
    segment: medicaid_mco
    granularity: plan
    formats: [pdf]
    status: maybe
"""


def test_bundled_registry_is_consistent():
    """The registry shipped with the package has no consistency problems."""
    assert validate_registry(load_registry()) == []


def test_registry_covers_target_parents():
    """All parent companies from the project outline are represented."""
    parents = {s.parent_org for s in load_registry()}
    expected = {
        "UnitedHealth Group",
        "Humana",
        "CVS Health",
        "Kaiser Permanente",
        "Elevance Health",
        "Centene",
        "Molina Healthcare",
    }
    assert expected <= parents


def test_seed_sources_exist_in_registry(seed):
    """Every source_id used in the seed data is registered."""
    ids = {s.id for s in load_registry()}
    assert set(seed["source_id"]) <= ids


def test_get_source():
    """Sources can be looked up by id; unknown ids raise KeyError."""
    assert get_source("kaiser-ma").formats == ("pdf", "xml")
    with pytest.raises(KeyError):
        get_source("no-such-source")


def test_registry_frame_columns():
    """The DataFrame view has one row per source and flattened formats."""
    frame = registry_frame()
    assert len(frame) == len(load_registry())
    assert {"id", "segment", "formats", "status"} <= set(frame.columns)
    assert "extra" not in frame.columns


def test_reference_datasets_have_join_keys():
    """Each reference dataset documents how it joins to the metrics."""
    refs = load_reference_datasets()
    assert {r["id"] for r in refs} >= {"cms-ma-enrollment-by-contract", "cms-ma-plan-directory"}
    assert all(r.get("join_key") and r.get("url") for r in refs)


def test_validate_registry_reports_problems(tmp_path):
    """Bad enums, unknown formats, duplicate ids and missing URLs are reported."""
    path = tmp_path / "registry.yaml"
    path.write_text(BAD_REGISTRY)
    sources = load_registry(path)
    problems = " | ".join(validate_registry(sources))
    for expected in ("duplicate id", "segment", "granularity", "status", "formats", "no URL"):
        assert expected in problems


def test_empty_registry_file(tmp_path):
    """An empty file yields no sources rather than an error."""
    path = tmp_path / "empty.yaml"
    path.write_text("")
    assert load_registry(path) == []
    assert load_reference_datasets(path) == []
