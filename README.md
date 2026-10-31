# OrgScope

Vue 3 and TypeScript application for the Dayforce assessment. Explore reporting lines, analyze workforce salary costs, and preview reporting changes using the supplied **data data.csv** (40,000 employees).

## Run

Requires Node.js 22 and npm. On Windows use npm.cmd if PowerShell blocks npm.ps1.

```sh
npm ci
npm run dev
```

Choose **Explore Giga Corp** to load the supplied dataset. Uploads accept the same assessment format.

```sh
npm run lint
npm run typecheck
npm test
npm run build
npm run audit:math
```

The mathematical audit compares every employee's metrics and three reporting moves against an independent Python Decimal reference. Python 3 is required. Browser regression checks require Playwright and a running production preview on port 4173:

```sh
python scripts/check_assessment.py
```

Set AUDIT_BASE_URL to override http://127.0.0.1:4173. Set QA_BROWSER to chromium, firefox, or webkit.

## Data and calculations

Required columns: `Employee Id`, `Manager`, `Name`, `Salary`. Optional displayed fields: `Department`, `Job Title`, `Location`. The original file is bundled directly; there is one source of dataset truth.

IDs must be unique. Blank Manager identifies a root. Missing managers, cycles, malformed CSV, missing identities and invalid salaries reject the import. A failed import preserves the previous organization.

Source salary decimals round half-up to cents per employee using decimal text and integer arithmetic. Costs use annual base Salary and exclude Bonus. The file supplies no currency: XXX represents unspecified currency internally; amounts display without a currency symbol.

Explorer metrics exclude the selected employee: descendant count, descendant managers, management salary cost, IC salary cost and their total. Management cost ratio is IC cost divided by manager cost, or N/A when manager cost is zero. Managers are identified by actual direct reports. Analytics include the selected leader. Scenario previews preserve total salaries and headcount and do not mutate the baseline.

## Architecture

The import worker validates CSV and builds indexed organization Maps. An iterative leaf-to-root traversal computes aggregates in O(n). Worker messages arrive in bounded batches and publish atomically. The explorer caps chart rendering at 150 cards, pages reports, and virtualizes navigator rows. Analytics traverse the selected subtree. The planner previews one reporting change and exports a JSON summary.

Employee data is processed in the browser. Uploads and scenarios are not persisted across refreshes. Hosting and the Loom walkthrough are separate submission steps.

## Exploration controls

Chart cards show descendants and non-leaf descendants. The inspector and Analytics offer **Show exact salary amounts** to display two decimal places after per-employee rounding. Metric definitions explain the descendant-only Explorer scope and leader-inclusive Analytics scope.

Expand or collapse a card without shifting its screen position. Reports per page supports 2, 4, 8, or 24 people. Use Organization to return to the current root; Show full path expands long breadcrumb trails.

Analytics branches can be ordered by annual salary cost, headcount, or management cost share. Select a branch to analyze its subtree, or choose Explore in chart to open that team in Explorer.

Imports report downloading, reading, validation/calculation and preparation stages. Employee counts track actual assembled records. Failed imports offer Retry import and preserve the current valid organization.

The browser regression script verifies CSV-derived metrics, visible card counts, exact costs, zero-denominator ratios, anchored expansion, pagination, search, breadcrumbs, Analytics ordering and chart navigation, failed imports/retries and mobile dialog navigation.

Employee names, job titles and departments lead the interface. Full IDs appear under Employee ID in the inspector with a Copy ID button; searches still accept IDs.
