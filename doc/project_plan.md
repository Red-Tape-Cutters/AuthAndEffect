# Project Plan and Status

Assumes the final presentation is around the week of **Dec 7, 2026** — adjust to the syllabus.

## Week 1 (Oct 30 – Nov 6): data spike and setup — ✅ done

- [x] Locate PA metric reports for target payers → `registry.yaml` (14 sources, 7 parents)
- [x] Transcribe complete reports → `seed_metrics_2025.csv` (now 5 entities, 66 rows, all validated)
- [x] Define target schema v0.1 → `schema.py`, `doc/schema.md`
- [x] Repo scaffold, `pyproject.toml`, MIT license, `.gitignore`
- [x] Validation rules, data loader, registry loader, CLI (`sources`, `summary`, `validate`)
- [x] Tests (64) with 99% coverage; ruff lint + format; GitHub Actions on Python 3.10–3.12
- [x] Functional spec draft, data inventory

**Remaining week-1 items for the team:**

- [ ] Create the GitHub repo `authandeffect`, push, confirm CI is green, protect `main`
- [ ] Fill in team names in `README.md`
- [x] Find Elevance reports (Wellpoint H8849 and Anthem NY Medicaid added to seed, 2026-11-03)
- [ ] Confirm `uhc-medicaid` and `aetna-ma` URLs; download Anthem MA PDFs by hand
- [ ] Decide open questions in `doc/data_inventory.md` §6

## Week 2 (Nov 6–13): design and technology review

1. Component specification (`doc/component_spec.md`): registry, fetcher, parsers,
   validator, enrichment (join), visualization, CLI — inputs/outputs of each.
2. Technology review: **pdfplumber vs camelot vs PyMuPDF** on Humana, Wellcare and the UHC
   combined PDF. Measure: tables found correctly, lines of code, speed, install pain.
3. Grow the registry to about 15–20 entries with `status: located`.

## Week 3 (Nov 13–20): core pipeline

1. `fetch.py`: download to `data/raw/`, SHA-256, skip unchanged files.
2. `parsers/`: CMS-template parser (Humana/Wellcare/Aetna), Kaiser XML, Molina HTML.
3. Fixture files in `test/fixtures/`; CI never touches the network.
4. Milestone: `authandeffect build` produces a validated CSV for ≥ 8 payers.

## Week 4 (Nov 20–27, Thanksgiving): enrichment

1. Load CMS Monthly Enrollment by Contract and MA Plan Directory.
2. `pa.aggregate(df, by="parent_org", weight="enrollment")`.
3. Test: reproduce KFF's direction of results for the same insurers.
4. Release dataset v0.1.

## Week 5 (Nov 27 – Dec 4): user-facing layer

1. `plot.py` (library chosen in week 2), example notebook for use cases 1–2.
2. Docstring pass, coverage ≥ 80% maintained.

## Week 6 (Dec 4–11): freeze and present

1. Feature freeze ≈ Dec 6. README, final docs, slides → PDF in `doc/`.
2. Timed dry run; recorded demo as backup.
