# Target Schema v0.1 — Data Dictionary

Defined in code in `src/authandeffect/schema.py`; enforced by `src/authandeffect/validate.py`.

## Shape

**Long (tidy) format:** one row per
`(reporting_year, source_id, entity_id, state, request_type, metric)` — this tuple is the
unique key. Use `authandeffect.to_wide()` for one row per entity × request type.

Why long: payers report different optional metrics, at different levels, with or without
counts. A wide table would be mostly empty columns and would need a schema change for every
new optional metric (CMS has already proposed adding metrics in CMS-0062-P).

## Columns

| Column | Type | Required | Description |
|---|---|---|---|
| `reporting_year` | int | ✅ | Calendar year the metrics cover (2025 = first year) |
| `parent_org` | str | ✅ | Parent company, e.g. `Centene` |
| `brand` | str | ✅ | Name on the report, e.g. `Wellcare` |
| `segment` | enum | ✅ | `medicare_advantage`, `medicaid_mco`, `chip_mco`, `medicaid_ffs`, `chip_ffs`, `qhp_ffe` |
| `entity_level` | enum | ✅ | `contract`, `plan`, `state`, `issuer`, `region` |
| `entity_id` | str | ✅ | MA contract (`H0029`), plan id, state code, or issuer id |
| `state` | str | | Two-letter state when the report is state-specific; blank for multi-state contracts |
| `request_type` | enum | ✅ | `standard`, `expedited`, or `all` (not split in source) |
| `metric` | enum | ✅ | See below |
| `count` | int | | "How many times this happened", when reported |
| `denominator` | int | | "Out of total …", when reported (requests or appeals) |
| `value` | float | ✅ | The reported figure |
| `unit` | enum | ✅ | `pct` for percentage metrics; `days` or `hours` for times |
| `reported_text` | str | | Original text for values that needed interpretation, e.g. `1 Days 0 Hours` |
| `source_id` | str | ✅ | Registry id, e.g. `centene-ma` |
| `source_url` | str | ✅ | The exact document the value came from |
| `retrieved_on` | date | | Date the document was read |
| `notes` | str | | Caveats specific to this row |

## Metric vocabulary

| Metric | Unit | Required by CMS-0057-F | Denominator |
|---|---|---|---|
| `approved` | pct | ✅ | requests |
| `denied` | pct | ✅ | requests |
| `approved_after_extension` | pct | ✅ | requests (some payers: extended requests) |
| `approved_after_appeal` | pct | ✅ | appeals |
| `mean_decision_time` | days/hours | ✅ | — |
| `median_decision_time` | days/hours | ✅ | — |
| `denied_after_extension` | pct | optional | |
| `denied_after_appeal` | pct | optional | appeals |
| `approved_within_timeframe` | pct | optional | approved requests |
| `denied_within_timeframe` | pct | optional | denied requests |

## Validation rules

| Rule | Severity | Check |
|---|---|---|
| `required_value` | error | Required columns are non-blank |
| `enum` | error | `segment`, `entity_level`, `request_type`, `metric` in vocabulary |
| `unit_mismatch` | error | `pct` for percentage metrics; `days`/`hours` for times |
| `pct_range` | error | 0 ≤ percentage ≤ 100 |
| `negative_time` | error | Times ≥ 0 |
| `count_exceeds_denominator` | error | `count ≤ denominator` |
| `pct_matches_counts` | error | `|100·count/denominator − value| ≤ 0.01` |
| `zero_denominator` | warning | Denominator is 0 ("0 out of 0") |
| `approve_deny_sum` | warning | `approved + denied` within 0.05 of 100 |
| `duplicate_key` | error | Key tuple is unique |

Whole-number sources (e.g. Molina) usually omit counts, so `pct_matches_counts` does not apply
to them; if they ever add counts, pass a larger `pct_tolerance`.

## Versioning

`SCHEMA_VERSION = "0.1.0"`. Adding a metric to the vocabulary is a minor version bump;
renaming or removing a column is a major one.
