# Data Inventory — Week 1 Data Spike

*Compiled 2026-10-30; Elevance added 2026-11-03. Machine-readable version: `src/authandeffect/data/registry.yaml`.*

The goal of the spike was to answer the riskiest question first: **can we actually find and
read the reports for the insurers in our outline, and at what level of detail?**

**Answer: yes for all of them.** 14 payer sources registered across all 7 parent companies
in the outline; 8 located, 6 partial, none missing. Five reports (four MA contracts and one
Medicaid issuer) were transcribed in full into the seed dataset and pass validation.

## 1. Payer sources

| Source id | Parent → brand | Segment | Level | Format | Status | Key observation |
|---|---|---|---|---|---|---|
| `uhc-ma` | UnitedHealth → UnitedHealthcare | MA | contract | PDF (one combined) | located | All H-contracts in one PDF; third-party (FTI) review noted |
| `uhc-medicaid` | UnitedHealth → UHC Community Plan | Medicaid | plan | PDF | partial | Found only on a "preview" subdomain; confirm live URL |
| `humana-ma` | Humana | MA | contract | PDF per contract | located | **Predictable URL pattern** `Humana_{contract}_Prior_Auth_Metrics_PlanYear2025pdf` |
| `humana-medicaid` | Humana Healthy Horizons | Medicaid | plan | PDF per state | located | Same layout as MA; seen VA, OH, LA, SC, KY |
| `aetna-ma` | CVS → Aetna Medicare | MA | contract | PDF | partial | Index page from a third-party source, not yet opened; D-SNP example follows CMS template |
| `aetna-medicaid` | CVS → Aetna Better Health | Medicaid | plan | PDF per state | located | Adds a "Key Highlights" box above template tables |
| `kaiser-ma` | Kaiser Permanente | MA (+ Medicaid, QHP sections) | region → contract | **PDF + XML** | located | Only major MA payer seen with a machine-readable file |
| `elevance-ma` | Elevance → Anthem BCBS | MA | contract | PDF per contract | partial | URL pattern `{contract}-medicare-prior-auths-metrics.pdf`; **anthem.com blocks automated fetching (robots.txt)**, so download by hand |
| `wellpoint-ma` | Elevance → Wellpoint | MA | contract | PDF per contract | located | Same pattern on wellpoint.com; percentages only, no counts; times unit-less (footnote: days) |
| `elevance-medicaid` | Elevance → Anthem / Wellpoint | Medicaid | issuer | PDF / HTML | partial | NY PDF on anthembluecross.com (issuer G0606, all plans); VA is an HTML page on anthem.com (blocked) |
| `centene-ma` | Centene → Wellcare | MA | contract | PDF per contract | located | Consistent layout; URL state prefix is **not** reliable |
| `centene-medicaid` | Centene → state plans | Medicaid | plan | PDF | partial | One page per state brand (Health Net CA, SilverSummit NV, …) |
| `molina-medicaid` | Molina | Medicaid | plan | **HTML table** | located | Whole-number percentages, times in hours, no counts |
| `molina-ma` | Molina / Senior Whole Health | MA | contract | HTML | partial | Molina is leaving MAPD in 2027 |

## 2. What the seed transcription taught us

We transcribed five complete reports (66 rows) into `seed_metrics_2025.csv`:
Wellcare H0029, Humana H1468, Kaiser Washington H5050, Wellpoint H8849 (all MA) and Anthem
NY Medicaid issuer G0606. Findings that shaped the schema:

1. **Granularity is contract-level for MA, as CMS guidance says.** So joining to CMS
   enrollment by contract number is feasible — the main join of the project is confirmed.
2. **Counts are often reported, but not always.** Wellcare, Humana and Kaiser publish counts,
   so every one of their percentages is verified (`pct_matches_counts`). Elevance publishes
   percentages only, so its request volumes are unknown and enrollment weighting matters more.
3. **Time units and precision differ:**

   | Payer | Standard mean | Expedited mean | Precision |
   |---|---|---|---|
   | Wellcare | "5 days" | "1 days" | whole days, even for a 72-hour limit |
   | Humana | "1 day(s)" | "9 hour(s)" | days / hours |
   | Kaiser | "1 Days 0 Hours" | "0 Days 17 Hours" | days + hours |

   → store the original text in `reported_text`, normalize to hours in analysis.
   A Wellcare median of "3 days" can mean anything from 60 to 84 hours, so cross-payer
   time comparisons need a caveat.
4. **Appeals are not always split by request type.** Humana reports one appeal table
   (allowed by the CMS template). → `request_type = "all"`.
5. **"0 out of 0" is common** for extension metrics. → a *warning*, not an error.
6. **Optional metrics vary.** Kaiser adds "approved within 14 days / 72 hours" and "denied
   after appeal". → long format absorbs these without empty columns.
7. **Elevance's "Scorecard" layout** prints times with no unit; only a footnote ("1 day
   means up to 24 hours") says they are days. Appeal and extension rows are not split by
   request type. → `unit = days`, `request_type = all` where needed, caveat in `notes`.
8. **Labels can be misleading.** Wellcare's appeal row says "out of total requests" but the
   denominator is the number of appeals. → recorded in `notes`.

## 3. Parsing difficulty (input to the week-2 technology review)

| Layout | Payers | Expected approach | Difficulty |
|---|---|---|---|
| Elevance "Scorecard" PDF (numbered list, no tables) | Anthem, Wellpoint | Text extraction + label regex | Low |
| CMS template PDF, one entity per file | Humana, Wellcare, Aetna, Centene plans | Text extraction + regex on table rows ("Requests Approved 21,801 26,108 83.50%") | Low–medium |
| Combined PDF, many contracts | UnitedHealthcare | Table extraction, split by contract header | Medium–high |
| Wide multi-contract tables | Kaiser | XML first; PDF table extraction as fallback | Low (XML) |
| HTML table in web page | Molina | `pandas.read_html` | Low |

Interesting: several PDFs repeat every number in a sentence summary ("In 2025, … received a
total of 26,108 standard … requests"), giving a second, independent extraction path for
cross-checking.

**Recommended week-2 tech review:** compare **pdfplumber vs camelot vs PyMuPDF** on three real
PDFs (one Humana, one Wellcare, the UHC combined file).

## 4. Join datasets

| Dataset | Publisher | Granularity | Join key | Purpose |
|---|---|---|---|---|
| Monthly Enrollment by Contract | CMS | contract × month | contract number | Enrollment weights |
| MA Plan Directory | CMS | contract | contract number | Contract → parent org |
| Health Plan Prior Authorization Data (stretch) | Washington State, data.wa.gov | carrier × service category | carrier name | Service-level contrast |

URLs are in `registry.yaml` under `reference_datasets`.

## 5. Similar tools and analyses (checked for overlap)

| Project | What it is | How we differ |
|---|---|---|
| KFF analysis (Aug 13, 2026) | Report on 14 insurers; enrollment-weighted using CMS Dec 2025 enrollment | Static analysis, no reusable code → we can reproduce it as a validation test |
| Artificer Health compliance scorecard | Tracks *whether* ~1,300 payers posted; JSON of publication status | Tracks compliance, not the metric values |
| authandeffector.netlify.app dashboard | Plan-level dashboard with per-row source links | Web dashboard, no package/schema; some figures unverified |
| theauthandeffect.com, healthbillcentral.com | Lists/blog tables of payer metrics | No pipeline, no validation, no join |

Our differentiation: installable package, documented schema, validation rules, provenance on
every row, enrollment join, and a maintainer workflow for future years.

## 6. Open questions for the team

1. Scope: MA only for the MVP, Medicaid second? (Recommended: yes — MA has the clean contract
   join.)
2. Confirm production URLs for `uhc-medicaid` and `aetna-ma`. Get a list of Elevance MA
   contracts from the CMS plan directory, then download the anthem.com PDFs by hand.
3. Do we treat Kaiser's per-region report as one source with many contracts (current) or one
   source per region?
4. Commit raw PDFs? Recommended **no** — commit URLs + SHA-256 hashes; keep 2–3 small fixture
   files in `test/fixtures/` only for parser tests.
