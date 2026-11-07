"""Source registry: where each payer publishes its PA metrics, and in what form.

Finding a payer's report is a manual, human-curated step (there is no central index), so
the registry is a YAML file reviewed by the team. Later stages (fetcher, parsers) read
this registry to know what to download and which parser to apply.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from importlib import resources
from pathlib import Path

import pandas as pd
import yaml

from authandeffect.schema import ENTITY_LEVELS, SEGMENTS

REGISTRY_FILE = "registry.yaml"

FORMATS = ("pdf", "html", "xml", "xlsx", "csv")
STATUSES = ("located", "partial", "not_located")


@dataclass(frozen=True)
class Source:
    """One place where a payer publishes PA metrics for one market segment.

    Attributes:
        id: Short unique identifier, e.g. ``"humana-ma"``.
        parent_org: Parent company, e.g. ``"Humana"``.
        brand: Brand or subsidiary name shown on the report.
        segment: Market segment (see :data:`authandeffect.schema.SEGMENTS`).
        granularity: Reporting level (see :data:`authandeffect.schema.ENTITY_LEVELS`).
        formats: File formats the reports use.
        status: ``located``, ``partial`` (some reports found) or ``not_located``.
        index_url: Landing page that links the reports, when known.
        example_url: One concrete report, used for parser development.
        url_pattern: Template for per-entity URLs, with ``{placeholders}``.
        parser: Name of the parser to use (filled in from week 3 on).
        notes: Free-text observations from the data spike.
    """

    id: str
    parent_org: str
    brand: str
    segment: str
    granularity: str
    formats: tuple[str, ...]
    status: str
    index_url: str = ""
    example_url: str = ""
    url_pattern: str = ""
    parser: str = ""
    notes: str = ""
    extra: dict = field(default_factory=dict, compare=False, repr=False)


_SOURCE_FIELDS = {
    "id",
    "parent_org",
    "brand",
    "segment",
    "granularity",
    "formats",
    "status",
    "index_url",
    "example_url",
    "url_pattern",
    "parser",
    "notes",
}


def _read_yaml(path: str | Path | None) -> dict:
    if path is None:
        text = (resources.files("authandeffect") / "data" / REGISTRY_FILE).read_text("utf-8")
    else:
        text = Path(path).read_text("utf-8")
    return yaml.safe_load(text) or {}


def _to_source(entry: dict) -> Source:
    known = {k: v for k, v in entry.items() if k in _SOURCE_FIELDS}
    extra = {k: v for k, v in entry.items() if k not in _SOURCE_FIELDS}
    known["formats"] = tuple(known.get("formats") or ())
    for key in ("index_url", "example_url", "url_pattern", "parser", "notes"):
        known[key] = (known.get(key) or "").strip()
    return Source(**known, extra=extra)


def load_registry(path: str | Path | None = None) -> list[Source]:
    """Load payer sources from the registry YAML.

    Args:
        path: Registry file; defaults to the copy bundled with the package.

    Returns:
        The payer sources in file order.
    """
    return [_to_source(e) for e in _read_yaml(path).get("payer_sources", [])]


def load_reference_datasets(path: str | Path | None = None) -> list[dict]:
    """Load the non-payer datasets (enrollment, plan directory) used for joins.

    Args:
        path: Registry file; defaults to the copy bundled with the package.

    Returns:
        A list of dicts with at least ``id``, ``name``, ``url`` and ``join_key``.
    """
    return list(_read_yaml(path).get("reference_datasets", []))


def get_source(source_id: str, sources: list[Source] | None = None) -> Source:
    """Look up one payer source by id.

    Args:
        source_id: The ``id`` field of the source.
        sources: Sources to search; defaults to :func:`load_registry`.

    Returns:
        The matching source.

    Raises:
        KeyError: If no source has that id.
    """
    for source in sources if sources is not None else load_registry():
        if source.id == source_id:
            return source
    raise KeyError(f"unknown source id: {source_id!r}")


def validate_registry(sources: list[Source]) -> list[str]:
    """Check registry entries for consistency.

    Args:
        sources: Output of :func:`load_registry`.

    Returns:
        Human-readable problems; an empty list means the registry is consistent.
    """
    problems = []
    seen = set()
    for s in sources:
        if s.id in seen:
            problems.append(f"{s.id}: duplicate id")
        seen.add(s.id)
        if s.segment not in SEGMENTS:
            problems.append(f"{s.id}: unknown segment {s.segment!r}")
        if s.granularity not in ENTITY_LEVELS:
            problems.append(f"{s.id}: unknown granularity {s.granularity!r}")
        if s.status not in STATUSES:
            problems.append(f"{s.id}: unknown status {s.status!r}")
        bad_formats = [f for f in s.formats if f not in FORMATS]
        if bad_formats:
            problems.append(f"{s.id}: unknown formats {bad_formats}")
        if s.status == "located" and not (s.index_url or s.example_url):
            problems.append(f"{s.id}: status is 'located' but no URL is recorded")
    return problems


def registry_frame(sources: list[Source] | None = None) -> pd.DataFrame:
    """Return the registry as a DataFrame (one row per source).

    Args:
        sources: Sources to convert; defaults to :func:`load_registry`.

    Returns:
        A DataFrame whose ``formats`` column is a comma-separated string.
    """
    rows = []
    for s in sources if sources is not None else load_registry():
        row = asdict(s)
        row.pop("extra")
        row["formats"] = ",".join(s.formats)
        rows.append(row)
    return pd.DataFrame(rows)
