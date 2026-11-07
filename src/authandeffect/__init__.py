"""authandeffect: an open dataset and toolkit for insurer prior authorization metrics.

Since March 31, 2026, Medicare Advantage organizations, Medicaid and CHIP programs and
managed care plans, and QHP issuers on the federal exchanges must post annual prior
authorization (PA) metrics on their own websites under CMS-0057-F. Every payer uses its
own layout. This package defines one target schema for those metrics, a curated registry
of where each payer publishes, validation rules, and helpers to analyze the result.

Typical use::

    import authandeffect as pa

    df = pa.load_seed()                 # long/tidy format, one row per metric
    issues = pa.validate_metrics(df)    # data-quality checks
    wide = pa.to_wide(df)               # one row per entity x request type
"""

from authandeffect.data import denial_rates, load_seed, read_metrics, to_wide
from authandeffect.registry import get_source, load_reference_datasets, load_registry
from authandeffect.schema import SCHEMA_VERSION, parse_duration, to_hours
from authandeffect.validate import SchemaError, is_valid, validate_metrics

__version__ = "0.1.0"

__all__ = [
    "SCHEMA_VERSION",
    "SchemaError",
    "__version__",
    "denial_rates",
    "get_source",
    "is_valid",
    "load_reference_datasets",
    "load_registry",
    "load_seed",
    "parse_duration",
    "read_metrics",
    "to_hours",
    "to_wide",
    "validate_metrics",
]
