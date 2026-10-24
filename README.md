# OrgScope

A Vue 3, TypeScript, Tailwind CSS and Vite application for exploring reporting
hierarchies, workforce salary costs and hypothetical reporting changes. Built for
the Dayforce Product Engineer assessment. The bundled Giga Corp dataset contains
40,000 fictional employees; it is explicitly synthetic.

Source repository: [nati5174/OrgScope](https://github.com/nati5174/OrgScope)
(private; reviewers need repository access).

## Install and run

Requires Node.js 22 and npm. Use `npm.cmd` on Windows if PowerShell blocks npm.ps1.

```sh
npm ci
npm run dev
```

Open the URL printed by Vite (normally http://localhost:5173). Choose **Explore
Giga Corp** or upload a CSV. Build and preview the production artifact with:

```sh
npm run build
npm exec vite -- preview --host 127.0.0.1 --port 4173 --strictPort
```

The local preview is not a public deployment. No backend, account or database is
required. Employee data is processed locally in the browser.

## Features

- **Organization Explorer:** expandable reporting lines, report pagination,
  name/ID search, breadcrumbs, team focus, employee inspector and pan/zoom controls.
  Every non-control card surface selects its employee; buttons keep their actions.
- **Workforce Analytics:** branch cost comparisons, manager/IC cost and headcount
  shares, salary distributions, reporting depths and spans of control. Search or
  drill into any reporting subtree and return to the chart.
- **Scenario Planner:** preview one hypothetical team move, compare affected
  ancestors, explore original/proposed structures and export a JSON summary.
  Every preview starts from the baseline; reporting changes do not create salary
  savings. Changing selections marks an existing preview as stale.
- **Responsive interactions:** desktop navigator/inspector panels, native mobile
  dialogs, keyboard tree navigation, canvas controls and reduced-motion support.

## CSV contract and metric definitions

Required headers: `employee_id,manager_id,name,salary,currency`.
Optional headers: `department,title,location`.
See [dataset documentation](data/README.md) for examples.

IDs are strings and must be unique; names may repeat. A blank manager indicates
a root; multiple roots are supported. Missing managers, cycles, duplicate columns
or IDs, malformed CSV and empty identities reject the import. Salaries must be
nonnegative annual amounts with at most two decimal places, without currency
symbols or thousands separators. Use one uppercase three-letter currency per file.
Decimal text is converted exactly to integer cents, then individual and company
salary totals are checked against safe-number bounds. Errors display the first
20 issues; a failed import preserves the previous valid organization.

Explorer metrics **exclude the selected employee**:

| Metric | Definition |
| --- | --- |
| Descendants | All employees below the selected employee |
| Non-leaf descendants | Descendants with direct reports |
| Management cost | Annual salaries of descendant managers |
| IC cost | Annual salaries of descendant employees without direct reports |
| Total descendant cost | Management cost + IC cost |
| Management cost ratio | IC salary cost / manager salary cost; N/A at zero denominator |

Managers are identified by actual reports, not job titles. Analytics **include
the scope leader**, unlike Explorer descendant metrics. Analytics separately
label salary-cost and headcount ratios. Costs are annual base salaries; benefits
and other expenses are not inferred. Displayed currency rounds to whole units;
underlying cent calculations remain exact.

## Architecture

| Module | Responsibility |
| --- | --- |
| `src/engine/organization.ts` | CSV validation, domain types, indexing, aggregation and search |
| `src/engine/explorer.ts`, `navigator.ts`, `treeLayout.ts` | Bounded chart projection, navigation rows and D3 layout |
| `src/engine/analytics.ts`, `scenario.ts` | Pure scoped analytics and immutable scenario simulation |
| `src/workers/` | Read files and run the existing import engine off the UI thread |
| `src/services/importOrganization.ts` | Worker ownership, cancellation, chunk assembly and atomic publication |
| `src/composables/useExplorer.ts` | Selection, focus, expansion and reporting-page state |
| `src/components/` | Presentation, pointer/keyboard events and view-local state |
| `src/App.vue` | Dataset ownership, import lifecycle and workspace navigation |

The validated organization uses Maps, string IDs and integer-cent metrics. An
iterative leaf-to-root queue computes aggregates in O(n) time and space and detects
disconnected cycles. Metric lookup is O(1); selecting/focusing also walks ancestor
paths and reveals the corresponding navigator page. Search is a bounded-result
linear scan. Analytics traverse the selected scope and sort reporting branches.
Scenarios copy Map indexes in O(n), then update affected ancestor paths, sharing
unchanged records without mutating the original organization.

The organization is held in a shallow Vue ref. Chart rendering is capped at 150
cards, with four reports per page by default (eight/24 optional). D3 receives only
that projection. Navigator rows are virtualized; flattening a fully expanded
hierarchy still takes O(n) work. Layout computation is cached across selection.

File reading, parsing, validation and aggregation run in a module Web Worker.
Results arrive in batches of up to 500 employee/metric records or 1,000 edges.
The UI assembles private indexes and publishes only a complete result. Workers
terminate on completion, failure, cancellation or owner unmount. Superseded
imports cannot replace newer data; there is no synchronous fallback.

## Test and review

```sh
npm run lint
npm run typecheck
npm test
npm run build
npm exec tsx -- scripts/audit_math.ts
```

The current unit suite has 50 tests covering precision, validation, cycles,
40k-deep chains, layout, navigation, analytics, scenario invariants and worker
lifecycle/serialization. The mathematical audit requires Python 3 and uses an
independent CSV/Decimal ancestor-chain reference.

Browser checks require Python Playwright and installed engines:

```sh
python -m pip install playwright
python -m playwright install chromium firefox webkit
python scripts/run_browser_suite.py
python scripts/check_background_import.py
python scripts/check_card_selection.py
python scripts/check_analytics_replacement.py
python scripts/check_import_races.py
```

Run the production preview on port 4173 first. Generate the 100k fixture for
background/race checks with `node --expose-gc --import tsx scripts/audit_performance.ts`
if it is absent. `run_browser_suite.py` executes the
existing Explorer, Analytics and Scenario scripts across all three engines.
Those scripts also run individually with `AUDIT_BASE_URL` (default 5173) and
`QA_BROWSER`. Selection, import-race and analytics-replacement scripts default to
4173. The comprehensive five-size visual/axe audit is `scripts/audit_browser.py`;
set `AUDIT_BASE_URL=http://127.0.0.1:4173/` and a fresh `QA_OUTPUT_DIR` to preserve
historical evidence. Keyboard/readability checks use `QA_STAGE=after` with
`scripts/check_followup.py`.

[CODE_QUALITY_REVIEW.md](CODE_QUALITY_REVIEW.md) documents architecture findings,
justified changes, current verification and trade-offs. [AUDIT_REPORT.md](AUDIT_REPORT.md)
retains earlier correctness, browser, accessibility and performance evidence.
Use the dated reports for actual executed coverage, not a blanket compatibility
or accessibility guarantee.

## Performance and limitations

```sh
npm run benchmark
npm run benchmark:analytics
npm run benchmark:scenario
npm run benchmark:explorer
node --expose-gc --import tsx scripts/audit_performance.ts
python scripts/check_import_responsiveness.py
```

The Node audit generates 1k/10k/100k synthetic fixtures before browser performance
checks. Run benchmarks separately from other test workloads. Node timings exclude
file transfer and browser rendering. The UI footer shows dataset and currency;
processing timings remain available in benchmark/audit outputs.
Harnesses write measurements under `data/` and may replace earlier outputs; copy
artifacts or use supported output options when retaining a baseline.

Workers improve responsiveness but add startup/serialization overhead. UI index
assembly, Vue rendering, search, analytics and scenario preview still use the main
thread. Uploads have no size cap, and peak worker/UI memory overlap is unmeasured.
Automatic chart framing preserves readable cards; explicit Fit may shrink text,
and native scale can require panning to reach offscreen reports. Tree rows support
arrows, Home/End and Enter/Space; a focused canvas supports arrow panning and Home.

Imported organizations reset on refresh. Scenario previews support one move and
are not persisted. Workspace navigation is local state, not multiple URL routes.
Physical touch devices and screen readers have not been formally tested. The
original assessment CSV/schema remains unavailable and public hosting is not
configured; those delivery matters are separate from the local code-quality review.


## Source package contents

The repository includes application/test source, project documentation and the
synthetic CSV plus its generated summary. The assessment PDF, extracted assessment
text, raw audit evidence, screenshots and recorded benchmark outputs remain local
and are excluded from Git. Reports retain historical evidence links; those local
artifacts are intentionally absent from the GitHub source package. Running the
verification and benchmark scripts generates new local outputs under `data/`.
