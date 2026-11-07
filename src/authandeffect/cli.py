"""Command-line interface: ``authandeffect sources | summary | validate``."""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from authandeffect import __version__
from authandeffect.data import denial_rates, load_seed, read_metrics, to_wide
from authandeffect.registry import load_registry, registry_frame, validate_registry
from authandeffect.validate import SchemaError, is_valid, validate_metrics


def _cmd_sources(_args: argparse.Namespace) -> int:
    sources = load_registry()
    frame = registry_frame(sources)[["id", "segment", "granularity", "formats", "status"]]
    print(frame.to_string(index=False))
    problems = validate_registry(sources)
    for problem in problems:
        print(f"PROBLEM: {problem}", file=sys.stderr)
    return 1 if problems else 0


def _cmd_summary(args: argparse.Namespace) -> int:
    df = read_metrics(args.path) if args.path else load_seed()
    wide = to_wide(df)
    print(f"{len(df)} metric rows, {wide['entity_id'].nunique()} reporting entities\n")
    print("Standard-request denial rates (highest first):")
    print(denial_rates(df, "standard").to_string(index=False))
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        df = read_metrics(args.path) if args.path else load_seed()
        issues = validate_metrics(df)
    except (SchemaError, FileNotFoundError, pd.errors.ParserError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if issues.empty:
        print(f"OK: {len(df)} rows, no issues")
        return 0
    print(issues.to_string(index=False))
    counts = issues["severity"].value_counts().to_dict()
    print(
        f"\n{len(df)} rows; errors: {counts.get('error', 0)}, warnings: {counts.get('warning', 0)}"
    )
    return 0 if is_valid(issues) else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``authandeffect`` command.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(prog="authandeffect", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("sources", help="list payer sources in the registry").set_defaults(
        func=_cmd_sources
    )
    for name, func, text in (
        ("summary", _cmd_summary, "summarize a metrics file (default: bundled seed data)"),
        ("validate", _cmd_validate, "check a metrics file against the schema rules"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument("path", nargs="?", help="long-format metrics CSV")
        p.set_defaults(func=func)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 success, 1 validation errors, 2 unreadable input.
    """
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
