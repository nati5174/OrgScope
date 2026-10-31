# Assessment dataset verification

Verified October 30, 2026 against the supplied `data data.csv`, SHA-256 `a1614d2c34f9723e301e8f8a6ef17fbd91f729a7b73fa907fa825cb297ea9754`.

- All 51 unit tests passed across 9 files, including assessment import, worker serialization, hierarchy, analytics and scenario checks.
- Type checking and lint passed.
- Production build passed and bundled the supplied CSV.
- Expanded production browser regressions passed in Chromium and WebKit: CSV-derived costs and counts, camera anchoring, two-report pagination, search, full breadcrumbs, Analytics sorting and chart drill-through, invalid-upload preservation, failed-download retry, and mobile dialogs. No browser runtime errors. Firefox could not create a page in this environment; its coverage is unverified.
- Independent Python Decimal reference: all 40,000 employees verified, 480,000 baseline comparisons, zero mismatches.
- Three reporting moves: 600,000 additional metric comparisons, zero mismatches. Headcount, salaries and baseline preserved.

Total rounded base salary is 2,422,442,219.82 in unspecified currency. Each employee salary rounds half-up to cents before summation; Bonus is excluded.

Windows sandbox execution required Node preserve-symlinks flags and temporary native Vite/Vitest configurations under ignored data/audit. The mathematical audit ran from a TypeScript-transpiled temporary copy with unchanged calculations. Browser checks used the production preview on port 4173. These checks do not constitute a full accessibility audit.
