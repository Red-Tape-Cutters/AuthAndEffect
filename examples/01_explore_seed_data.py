"""Example: load, validate and compare the bundled 2025 seed data.

Run from the repository root after ``pip install -e .``::

    python examples/01_explore_seed_data.py

The seed holds five real reporting entities transcribed by hand from the insurers' own
CMS-0057-F reports: four Medicare Advantage contracts (Wellcare H0029, Humana H1468,
Kaiser WA H5050, Wellpoint H8849) and Anthem's New York Medicaid issuer (G0606).
"""

import pandas as pd

import authandeffect as pa


def main() -> None:
    """Walk through the main package functions on the seed data."""
    pd.set_option("display.width", 120)

    # 1. Load the long-format table: one row per contract x request type x metric.
    df = pa.load_seed()
    print(f"Loaded {len(df)} rows for contracts {sorted(df['entity_id'].unique())}\n")

    # 2. Check data quality. Warnings ("0 out of 0") are expected; errors are not.
    issues = pa.validate_metrics(df)
    print("Validation summary:", issues.groupby(["severity", "rule"]).size().to_dict())
    print("Valid (no errors):", pa.is_valid(issues), "\n")

    # 3. Compare standard-request denial rates across insurers.
    print("Standard prior authorization requests, share denied:")
    print(pa.denial_rates(df, "standard").to_string(index=False), "\n")

    # 4. Wide view with decision times converted to hours, so payers that report in
    #    days and payers that report in hours line up.
    wide = pa.to_wide(df)
    cols = [
        "brand",
        "entity_id",
        "request_type",
        "denied_pct",
        "approved_after_appeal_pct",
        "median_decision_time_hours",
    ]
    print("Side by side (times in hours):")
    print(wide[cols].to_string(index=False), "\n")

    # 5. Duration strings from different payers parse to one unit.
    for text in ["1 Days 0 Hours", "9 hour(s)", "5 days"]:
        print(f"{text!r:>18} -> {pa.parse_duration(text):g} hours")


if __name__ == "__main__":
    main()
