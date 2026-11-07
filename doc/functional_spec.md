# Functional Specification — `authandeffect`

*Draft v0.1, week 1 (2026-10-30). Project type: **tool project** (Python package + open dataset).*

## 1. Background

Prior authorization (PA) requires a clinician to get an insurer's approval before a service is
covered. It is one of the most visible sources of friction in US health insurance, yet until
recently there was no public, insurer-by-insurer data on how often requests are denied or how
long decisions take.

The CMS Interoperability and Prior Authorization final rule (**CMS-0057-F**, January 2024)
changed that. Since **March 31, 2026**, "impacted payers" must post annual PA metrics for the
previous calendar year on a public page of their own website. Impacted payers are:

- Medicare Advantage (MA) organizations
- State Medicaid and CHIP fee-for-service programs
- Medicaid managed care plans and CHIP managed care entities
- Qualified Health Plan (QHP) issuers on the federally facilitated exchanges

Employer and other commercial plans are **not** covered.

For each segment, payers report a list of items and services that need PA (drugs excluded),
plus, aggregated across all those items and services:

| Required metric | Request types |
|---|---|
| % of requests approved | standard, expedited |
| % of requests denied | standard, expedited |
| % approved after the review time was extended | standard, expedited |
| % approved after appeal | combined or split |
| Mean and median time from submission to decision | standard, expedited |

**The problem.** The first round of reports (CY2025 data) proved hard to use:

- There is no central index. Each payer posts somewhere on its own site, often several
  clicks deep.
- A CMS template exists but is optional, so layouts vary: per-contract PDFs (Humana, Wellcare),
  one combined PDF (UnitedHealthcare), per-region PDF plus XML (Kaiser), HTML tables embedded in
  provider pages (Molina).
- Units and precision differ. Times appear as "5 days", "9 hour(s)" or "1 Days 0 Hours";
  percentages have two decimals or none; counts are sometimes missing.
- Reporting levels differ: MA by contract, Medicaid by plan or state.

Analysts at KFF had to collect the reports by hand for their August 2026 analysis. Researchers,
advocates and consumers who want to compare insurers face the same manual work every year.

**Our goal.** Build `authandeffect`, a Python package that turns these scattered reports into one
standardized, validated, documented dataset, joined to public CMS enrollment data so that
contract-level figures can be weighted and rolled up to parent companies.

## 2. User profiles

| User | Domain knowledge | Computing skills | What they want |
|---|---|---|---|
| **Health policy researcher / data journalist** (primary) | Knows MA, Medicaid, and what a denial rate means; may not know CMS contract IDs | Comfortable in Python + pandas or R; uses Jupyter | A clean, citable table with provenance so they can analyze and publish |
| **Patient advocate / benefits counselor** | Knows plans and member pain points; not a data specialist | Can run a notebook or a CLI command from instructions; reads charts | Ranked, caveated comparisons of insurers in one state and segment |
| **Package maintainer / contributor** | Learns the reporting rule from our docs | Python developer; git, pytest | Add a payer or a new reporting year without touching core code |

People choosing a plan are an *indirect* audience: they benefit through advocates and
published comparisons, not by installing the package.

## 3. Data sources

### 3.1 Payer PA metric reports (core dataset)

- **What:** CY2025 metrics posted by each payer under CMS-0057-F.
- **Where:** Payer websites; locations recorded in `src/authandeffect/data/registry.yaml`
  (14 sources across 7 parent companies; see `doc/data_inventory.md`).
- **Granularity:** Annual. MA: per contract (e.g. H0029). Medicaid managed care: per plan or
  state. Kaiser: per region, broken out by contract.
- **Format:** Mostly PDF; some HTML tables; Kaiser also publishes XML.
- **Structure after standardization:** long/tidy table, one row per
  `(reporting_year, source, entity, request_type, metric)`, with value, unit, optional
  count and denominator, original text, and source URL. See `doc/schema.md`.
- **Access:** Public, no login (required by the rule). Raw files are cached locally and not
  committed; the standardized table and source URLs are.

### 3.2 CMS Monthly Enrollment by Contract (join dataset)

- **What:** Number of enrollees in each MA contract, published monthly by CMS.
- **Granularity:** Contract × month (different time granularity from 3.1).
- **Join key:** contract number (`entity_id`).
- **Use:** Weight contract-level rates by enrollment when aggregating to parent company and
  market level (the same method KFF used).

### 3.3 CMS MA Plan Directory (join dataset)

- **What:** Contract number → legal entity and parent organization.
- **Use:** Assign contracts to parent companies consistently (Wellcare → Centene, etc.).

### 3.4 Stretch: Washington State Health Plan Prior Authorization Data

- **What:** State-published PA data for carriers in Washington by service category
  (data.wa.gov).
- **Use:** Shows the service-level detail the federal metrics lack; joins on carrier name.

## 4. Use cases

### Use case 1 — Researcher builds an enrollment-weighted comparison

**Objective:** Compare standard-request denial rates across MA parent companies, weighted by
enrollment, and export a table with sources for a report.

**Interaction:**

1. User installs the package: `pip install authandeffect` (or from GitHub).
2. User loads the standardized data: `df = pa.load(segment="medicare_advantage", year=2025)`.
3. System returns a long-format DataFrame; every row carries `source_url`.
4. User checks quality: `issues = pa.validate_metrics(df)`. System returns a table of
   warnings (e.g. "0 out of 0") and errors; `pa.is_valid(issues)` is `True`.
5. User calls `pa.aggregate(df, by="parent_org", weight="enrollment")`.
6. System joins CMS enrollment by contract, computes weighted rates, and reports how many
   contracts and enrollees each figure covers.
7. User exports with `table.to_csv(...)` and cites the source list.

*Week 1 status:* steps 2 (as `load_seed()`), 3 and 4 work today on five reporting entities (four MA contracts and one Medicaid issuer).

### Use case 2 — Advocate compares insurers in one state

**Objective:** See which MA insurers operating in Washington deny the most requests and how
quickly they decide, with caveats shown.

**Interaction:**

1. User runs the example notebook or `authandeffect summary --state WA --segment medicare_advantage`.
2. System filters to reporting entities in WA and prints a ranked table: denial %, % overturned
   on appeal, median decision time converted to hours, number of requests.
3. System adds a caveat when figures are not comparable (e.g. a payer reports times in whole
   days, or omits counts).
4. User calls `pa.plot.rank(df, metric="denied")` to get a bar chart for a presentation.

*Week 1 status:* `authandeffect summary` and `pa.denial_rates()` work on the seed data;
state filter and plotting are planned.

### Use case 3 — Maintainer adds a payer

**Objective:** Add a payer not yet covered, or the CY2026 reports when they appear in 2027.

**Interaction:**

1. Maintainer adds an entry to `registry.yaml` (URL, format, granularity).
2. `authandeffect sources` lists the new entry and reports any registry problems.
3. Maintainer adds a parser (or reuses one, e.g. the CMS-template parser) and a fixture file.
4. `authandeffect build` downloads, parses and standardizes; `authandeffect validate` flags issues.
5. CI runs the parser tests against the fixture; nothing is fetched from the network in CI.

*Week 1 status:* steps 1, 2 and 4 (`validate`) work.

## 5. Programming interface (planned)

| Function / command | Purpose | Status |
|---|---|---|
| `pa.load_seed()` | Bundled hand-entered seed data | ✅ week 1 |
| `pa.read_metrics(path)` | Read any schema-conformant CSV | ✅ week 1 |
| `pa.validate_metrics(df)`, `pa.is_valid()` | Data-quality rules | ✅ week 1 |
| `pa.to_wide(df)` | One row per entity × request type, times in hours | ✅ week 1 |
| `pa.denial_rates(df, request_type)` | Ranked denial rates | ✅ week 1 |
| `pa.parse_duration(text)` | Normalize duration strings | ✅ week 1 |
| `pa.load_registry()`, `pa.get_source()` | Where each payer publishes | ✅ week 1 |
| `authandeffect sources / summary / validate` | CLI | ✅ week 1 |
| `pa.fetch(source_id)` | Download and cache raw reports | week 3 |
| `pa.parse(path, parser=...)` | Extract metrics from PDF/HTML/XML | week 3 |
| `pa.load(segment=, year=, state=)` | Load the full built dataset | week 3–4 |
| `pa.aggregate(df, by=, weight=)` | Enrollment-weighted roll-ups | week 4 |
| `pa.plot.*` | Rankings and comparisons | week 5 |

## 6. Non-goals and limitations

- Not a plan-shopping tool. Metrics are aggregated across all services, so they cannot tell a
  patient whether *their* procedure will be approved.
- No drug PA (excluded by the rule). No employer plans.
- We do not judge whether a denial was appropriate. Overturns on appeal can reflect new
  information, not a wrong first decision.
- Payer figures are self-reported and methods differ (e.g. which delegated vendors are
  included). We record differences in `notes` rather than "correct" them.
