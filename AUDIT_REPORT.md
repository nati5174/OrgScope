# OrgScope - Final Quality Audit

Audit date: 2026-10-23 (America/Toronto). Environment: Windows, Node v22.11.0, AMD Ryzen 5 PRO 7545U, Chromium 143.0.7499.4.

Follow-up completed on 2026-10-23: see section 13 for the worker import change, current cross-browser results, keyboard checks and before/after measurements. Sections 4-8 retain the original audit methodology and historical measurements where explicitly identified. Deployment and original-data access were excluded from the follow-up.

## 1. Executive summary

**Verdict: NOT READY TO SUBMIT.** The tested local application passes its technical checks after the original seven defects and subsequent confirmed issues were fixed. Section 16 records the P1 employee-card selection fix and its cross-browser regression evidence. Submission is blocked by the missing hosted application/reviewer source link. The original assessment spreadsheet is inaccessible, so its schema and real-data compatibility remain unverified. This verdict does not mean the local app is broken.

- Lint: PASS. Explicit TypeScript check: PASS. Production build: PASS.
- Current unit tests: **50 passed, 0 failed, across 8 files**, including nine worker parity/lifecycle cases. Original pre-audit baseline: 37 passed.
- Independent reference: 40,000/40,000 synthetic employees checked; 480,000 baseline comparisons; **0 mismatches**.
- Three scenario moves: 200,000 independent metric comparisons each; **0 mismatches**; headcount, salaries, and baseline isolation preserved.
- Earlier full follow-up production visual/accessibility audit: **120 screenshots, 81 axe scans, 0 reported violations and 0 browser errors** across Chromium, Firefox and WebKit; all nine existing interaction workflows pass.
- Clean installation: original audit verified 41 tests; the latest code-quality review repeated isolated npm ci, all 50 current tests and build after the Vitest security upgrade. See section 17.
- Production artifact tested at http://127.0.0.1:4173/. This is a local Vite preview, not a public deployment.

Original audit evidence: [final checks](data/audit/final-checks.json), [unit results](data/audit/unit-results.json), [independent math](data/audit/math-results.json), [browser audit](data/audit/browser-audit.json), [production smoke](data/audit/production-preview.json).

## 2. Dayforce requirements compliance matrix

The [original PDF](<Dayforce Product Engineer Intern - Screening Assessment.pdf>) was read. Its extracted text is retained in [assessment-extracted.txt](data/audit/assessment-extracted.txt). Additional product features are listed separately from mandatory assessment requirements.

| Requirement | Status | Implementation and evidence |
| --- | --- | --- |
| Vue.js and Tailwind CSS | PASS | Vue 3 SFCs, Vite/Tailwind configuration; clean install and production build in final-checks.json |
| Read employee CSV | PASS for documented schema; original schema UNVERIFIED | organization.ts; organization.test.ts and audit-regressions.test.ts; browser invalid-file cases |
| Approximately 40k employees | PASS on synthetic data; original data BLOCKED | math-results.json verifies 40,000 employees; four-size Node/browser performance results |
| Reporting hierarchy | PASS | Independent parent/root/direct-report/depth checks; explorer browser workflows |
| Expand and collapse | PASS | check_explorer.py: geometry, 24 reports, compaction, rapid toggles; audit_browser.py repeats across sizes |
| Descendant counts | PASS | All 40k IDs independently compared in math-results.json |
| Non-leaf descendant counts | PASS | All 40k IDs independently compared; non-leaf <= descendants invariant |
| Management, IC, total salary costs | PASS | Independent Decimal oracle; descendant-only values exclude selected employee |
| Management cost ratio | PASS for documented interpretation | IC descendant salary / manager descendant salary; N/A at zero denominator. Assessment formula remains ambiguous; headcount ratio is separately shown in analytics |
| Efficient per-path calculations | PASS with measured import limitation | O(n) iterative postorder; O(1) metric lookups; scenarios update affected paths; performance-node.json and performance-browser.json |
| Clean responsive interface | PASS in tested Chromium layouts | 1920x1080, 1440x900, 1280x800, 768x1024, 390x844 screenshots and browser assertions |
| Hosted project with inspectable code | FAIL / DELIVERY BLOCKER | No public application/source URL or hosting metadata identified. Project is not a Git repository. Local preview is not sufficient |
| Bonus organization cost view | PASS | Analytics checks for scoped costs, distributions, ratios, forests, and zero salaries |
| Added product features: search, navigator, inspector, focus | PASS | check_explorer.py, audit_browser.py, layout/state unit tests |
| Added stretch: hypothetical scenario planner | PASS | Scenario unit tests, independent oracle after three moves, check_scenario.py, browser/production populated previews |

## 3. Test coverage and results

Before production changes, npm run lint, npm test, and npm run build all succeeded. The four subsequently added adversarial regression cases all failed against the original code; [confirmed-defects-baseline.json](data/audit/confirmed-defects-baseline.json) preserves those failures. Axe also found contrast and visible-label/name problems: [axe-baseline.json](data/audit/axe-baseline.json).

| Check | Final outcome | Evidence |
| --- | --- | --- |
| ESLint | PASS, exit 0 | final-checks.json; npm run lint executed after fixes |
| TypeScript | PASS, exit 0 | npm run typecheck; build also runs vue-tsc --noEmit |
| Full Vitest suite | PASS: 50/50 | data/code-quality/final/unit-results.json |
| Production build | PASS, exit 0 | final-checks.json; production-preview.json loads final artifact |
| Clean npm ci + build + tests | PASS: install/build exit 0, 41/41 tests | isolated clean source copy verified; final-checks.json |
| Explorer interaction regressions | PASS | scripts/check_explorer.py; data/redesign/browser-results.json |
| Analytics regressions | PASS | scripts/check_analytics.py; unit analytics tests and browser-audit.json |
| Scenario regressions | PASS | scripts/check_scenario.py; scenario.test.ts, math-results.json |
| Five-size production browser/axe audit | PASS: 40 states captured, 27 scans with zero violations | browser-audit.json |
| Public deployment and reviewer source access | NOT EXECUTED: no URL available | no deployment is claimed |
| Firefox/WebKit | PASS for executed workflows and five-size audit | data/audit/followup/cross-browser-suite.json; followup/final-browser/browser-audit.json |

The suite covers empty input, single employees, multiple levels/roots, duplicate names, missing managers, duplicate IDs, cycles/self cycles, zero/decimal/invalid salaries, malformed CSV, quoting/BOM/newlines, deep 40k chains, wide teams, money precision, safe totals, key collisions, geometry, cached selection, and valid/invalid scenarios.

One existing unsafe-salary scenario test now asserts rejection at ingestion: the strengthened global precision invariant rejects that fixture before a scenario can be constructed. The rejection requirement was retained, not removed. Scenario comparisons against complete rebuilds remain in place.

During audit-tool development, an explicit TypeScript annotation was added to the benchmark run array after the type checker caught it. A dev-server hot-reload interrupted one screenshot run; the final complete run used the stable production preview. Intermediate failures were not treated as passes.

## 4. Mathematical correctness verification

Production uses bottom-up leaf-to-root aggregation. The reference in scripts/reference_metrics.py instead reads CSV with Python csv, parses money with Decimal, and walks each raw employee's ancestor chain, depositing that employee's count and salary into every ancestor. It imports no production calculation code.

For each of 40,000 IDs, scripts/audit_math.ts compares all five aggregate fields, exact parent, direct-report count, depth, cost ratio, cost reconciliation, non-leaf bound, and leaf behavior. Roots are checked separately. Per-chain seen sets detect cycles/repeated ancestors, and input IDs are independently checked for uniqueness.

- Employees with mismatches: **0**.
- Baseline comparison mismatches: **0**, across 480,000 comparisons.
- Descendant metrics always exclude the employee whose row is being inspected.
- management cost + IC cost = total descendant cost; leaf descendant metrics are zero.
- Manager classification uses actual direct reports, not job titles.
- Money is stored in integer cents; decimal text is converted exactly with BigInt before Number bounds checks. Displayed salaries are intentionally rounded to whole currency units; exact stored calculations retain cents.

Three independent modified-CSV references reassign GC000002 -> GC000007, GC000003 -> GC000006, and GC040000 -> GC000001. All five metrics for every employee are compared after each move: 600,000 additional comparisons and 0 mismatches. Repeated previews preserve the original metrics and global headcount/salary totals. Unit tests separately cover manager promotion/demotion, common ancestors, roots moving across a forest, self/descendant/no-op rejection, and deep paths.

## 5. Original dataset validation

**BLOCKED for the original assessment data.** The only supplied CSV is the explicitly synthetic Giga Corp file. The spreadsheet ID embedded in the PDF was retried through the connected Google Drive tool and returned HTTP 404. This does not establish whether the file was deleted or merely inaccessible to this connection. See [access result](data/audit/original-dataset-access.json).

Original-data metric mismatches: **NOT MEASURED**. Do not substitute the synthetic zero-mismatch result for original-data validation. The current importer requires employee_id, manager_id, name, salary, currency; original headers and salary conventions remain unknown.

The verified synthetic file SHA-256 is `9954b97db14b28ea1d33750f41261a21a04d4de6162cdcb61992541627b46107`. The source CSV was not modified by this audit. Audit-only 1k/10k/100k fixtures are separate files under data/audit/.

## 6. Performance and scalability

Node: ten sequential samples per size after a warmup; explicit GC available. Browser: five samples per size at 1440x900. p95 uses nearest rank: at these sample counts it equals the maximum, so it is a weak tail estimate. These are actual local measurements, not service-level guarantees. Other audit activity/background load may affect timings.

40k uses the supplied synthetic CSV. Other sizes use audit-only balanced 8-way synthetic trees, with fewer optional columns; cross-size results are not a controlled comparison of identical distributions. Raw runs and method details: [Node](data/audit/performance-node.json), [browser](data/audit/performance-browser.json).

The following Node/browser tables describe the **original synchronous-import build**, retained for historical comparison. Section 13 contains the matched before/after worker measurements; do not treat these earlier initial-render values as current worker timings.

### Node processing (median / p95 milliseconds)

| Employees | CSV parse | Build/index | Aggregate | Full-scan search | Analytics compute | Scenario compute | Bounded layout |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 6.0 / 8.8 | 1.3 / 1.7 | 0.6 / 0.9 | 0.2 / 0.7 | 0.8 / 3.3 | 0.3 / 0.9 | 1.3 / 4.2 |
| 10,000 | 37.3 / 55.9 | 20.6 / 31.7 | 5.8 / 39.3 | 0.7 / 1.4 | 8.2 / 19.5 | 8.9 / 18.5 | 1.7 / 2.4 |
| 40,000 | 201.8 / 228.3 | 112.1 / 131.6 | 42.9 / 54.8 | 9.8 / 13.1 | 33.1 / 58.9 | 49.3 / 72.3 | 1.4 / 5.5 |
| 100,000 | 390.5 / 420.4 | 283.9 / 342.9 | 99.9 / 122.2 | 15.8 / 23.0 | 59.3 / 76.2 | 125.5 / 151.2 | 1.7 / 2.1 |

### Browser interactions (median / p95 milliseconds)

Initial render is measured from file-change capture through matching DOM plus two animation frames, including file read, parsing, construction, and render. Other metrics start at an in-page input/click and end after two animation frames, excluding automation transport. They include frame scheduling and do not guarantee a completed paint.

| Employees | Initial render | Search | Expand | Collapse | Focus | Analytics render | Scenario preview |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 111.6 / 136.7 | 13.9 / 29.7 | 20.2 / 27.6 | 18.8 / 21.6 | 22.5 / 24.6 | 32.9 / 37.6 | 24.3 / 31.1 |
| 10,000 | 148.6 / 168.0 | 8.8 / 31.4 | 20.7 / 23.9 | 14.7 / 23.9 | 22.1 / 25.2 | 37.2 / 41.6 | 25.1 / 31.8 |
| 40,000 | 332.1 / 389.4 | 15.3 / 25.9 | 24.2 / 30.8 | 17.3 / 22.8 | 23.5 / 25.4 | 56.0 / 57.7 | 30.8 / 35.1 |
| 100,000 | 528.5 / 542.6 | 22.4 / 32.1 | 15.8 / 20.7 | 18.4 / 22.0 | 22.3 / 26.7 | 61.3 / 65.3 | 60.3 / 65.3 |

### Memory and DOM samples

| Employees | Node heap delta after load, median MiB | Node process RSS, median MiB | Browser JS heap after GC, median MiB | Browser DOM elements in sampled scenario state |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 2.5 | 75.5 | 4.6 | 403 |
| 10,000 | 12.1 | 113.9 | 7.2 | 403 |
| 40,000 | 51.1 | 193.2 | 18.1 | 398 |
| 100,000 | 117.8 | 295.9 | 29.9 | 403 |

Memory values are sampled, not peak memory. RSS is process-wide; browser heap and Node heap measure different environments. The DOM sample includes hidden mounted views, and is not the maximum during stress expansion. The explorer stress test separately enforces <=150 chart cards and fewer than 40 navigator DOM rows, including a 40k-level path.

Performance findings:

- No quadratic aggregation behavior was observed through 100k. Production metric preprocessing remains iterative O(n); selection reuses aggregate lookups and a cached chart projection. Independent geometry/state tests and browser layout-revision checks verify selection caching.
- Original import blocked the main thread (300-364 ms tasks at 40k, 477-515 ms at 100k). **Addressed in the follow-up:** file reading, parsing, validation, indexing and aggregation now execute in a worker. Main-thread result assembly/rendering still costs time; section 13 measures the remaining scheduling gaps and slower total import latency.
- Scenario map copies remain O(n), while metric updates touch affected ancestor paths. At 100k the measured Node scenario median is about 125 ms; browser preview median is about 60 ms in this run. These are different runtimes/measurement boundaries.
- A 20-cycle view/scenario retention check increased post-GC browser heap by 344,460 bytes (~0.33 MiB). This showed no large accumulation in that observation, but is not proof of leak freedom or a long-duration soak test. See [memory-cycle.json](data/audit/memory-cycle.json).

## 7. Browser and visual findings

The final five-size visual/axe run targets the built production preview. It covers initial chart, expanded tree, selected inspector, navigator, deep focus, analytics, empty planner, and populated planner: 8 states x 5 viewports = 40 screenshots. Every capture asserts no document-level horizontal overflow. All are listed in browser-audit.json.

Representative screenshots were visually inspected, rather than only generated: 1920 initial/analytics; 1440 expanded/focus; 1280 inspector/planner; 768 navigator/analytics; 390 initial/inspector/analytics. Final populated planner captures are also inspected. Geometry tests independently check card separation and that connector segments do not cross card interiors.

Findings: reporting connectors and panel separation are clear in tested layouts; long inspector content scrolls inside the panel. Text truncation on compact cards has title text/inspector access. Mobile chart branches outside the canvas require pan or Fit, by design; tables scroll within their panels. The follow-up confirmed 7.6-7.9px effective card-name text on short desktops and changed automatic framing to preserve readable scale. Explicit Fit can still shrink cards; automatic framing can leave reports outside the canvas, accessible by pan, keyboard or navigator. See section 13.

Interaction checks include repeated expand/collapse, a 24-report manager, duplicate names and exact IDs, nonexistent search, deep selection, cached layout, ancestor reveal, breadcrumbs, root return, keyboard tree/pan, zoom/fit/reset, state retention across repeated view changes, invalid-file retention, zero-salary/forest analytics, and scenario comparison/reset/export.

## 8. Accessibility and browser compatibility

Final result: **27 axe scans with 0 reported violations**, plus a production populated-scenario smoke scan with 0 violations. Fixes improve neutral/selected text contrast, use natural visible labels for cards/tree rows, and make horizontal scenario comparisons keyboard-focusable with an explicit focus ring. Native dialogs support Escape and focus trapping/return; reduced-motion behavior is checked.

Keyboard scrolling of the comparison table is explicitly verified at 768 and 390 widths. Explorer keyboard navigation is exercised with actual key events. Browser page-error capture reports zero errors in final runs.

Axe reports some incomplete contrast checks, especially for clipping/overlap/canvas contexts. These require judgment and are not equivalent to violations or a complete WCAG certificate. No screen-reader session, physical touch-device session, or formal target-size audit was performed.

Current executed coverage: **Chromium 143.0.7499.4, Firefox 144.0.2 and WebKit 26.0 PASS**. The follow-up installed missing engines and reran the existing interaction and five-size production audit suites. This does not establish compatibility with every browser/OS release or physical Safari device.

## 9. Confirmed defects discovered and fixed

| ID / severity | Reproduction / root cause | Small reliable fix | Regression evidence |
| --- | --- | --- | --- |
| Q01 / P0, fixed | Salary 90071992547409.90 was accepted but floating multiplication could store a cent incorrectly | Convert decimal text to BigInt cents, then enforce safe Number bounds | audit-regressions.test.ts; failing baseline and passing final test JSON |
| Q02 / P1, fixed | Root plus descendants could exceed safe whole-company totals even when descendant-only aggregates were safe; analytics could throw | Reject unsafe global totals during ingestion before replacing valid app state | Unit regression and browser invalid-file retention |
| Q03 / P2, fixed | Duplicate salary headers were silently renamed by Papa Parse and the first value used | Reject meta.renamedHeaders with an actionable duplicate-column error | Unit regression and five-size malformed import cases |
| Q04 / P2, fixed | Valid employee ID pager-r collided with a navigator pager key | Namespace both employee and pager keys; retain raw IDs for selection; update keyboard selectors consistently | Stable-key regression and full explorer keyboard/deep-path browser tests |
| Q05 / P2, fixed | Neutral/selected text had contrast ~4.26-4.42; populated scenario No change text had ~2.63 | Darken existing neutral text colors and localized scenario labels | axe-baseline.json; production-preview-initial-findings.json; final 27 scans |
| Q06 / P2, fixed | Custom accessible names omitted visible card/tree text | Use natural visible names and separate employee metadata descriptions | Baseline label-content-name-mismatch failures; final zero-violation scans |
| Q07 / P2, fixed | Populated narrow scenario table could not receive keyboard focus for horizontal scrolling | Add labelled focusable scroll region and focus indicator | Five-size populated-scenario axe regression and ArrowRight scroll assertion |

All confirmed application P0/P1 defects identified by this audit are fixed. No new product features or layout redesign were added. The remaining delivery blocker is separate from these application defects.

## 10. Remaining risks and limitations

1. Required hosted application plus inspectable source URL is missing. No external deployment was tested or published.
2. Original 40k dataset/schema is inaccessible (HTTP 404 via connected tool). Synthetic validation cannot prove original compatibility.
3. Chromium, Firefox and WebKit automated checks pass; physical devices, screen readers and other assistive technologies remain untested.
4. Worker import removes synchronous CSV computation from the UI thread. Main-thread assembly/rendering still has measured pauses, total completion latency increased, and uploads remain uncapped. See section 13; peak memory with worker/main-thread overlap was not measured.
5. Statistical tails use small sample counts; memory is sampled rather than peak, and retention testing is short.
6. Scenarios support one move at a time and are intentionally not persisted. Imported organization state resets on refresh; only / is a product route, and view navigation is local state.
7. The cost-ratio interpretation is documented but not confirmed by the assessment authors. The real importer schema may need adjustment once original data is available.
8. The clean install produced a deprecation warning for the pinned ESLint 9 toolchain. Lint/build/tests still pass; this is a development-maintenance item, not an application runtime failure.

## 11. Files changed and reproduction

Production changes:

- src/engine/organization.ts: exact cent parsing, duplicate-header rejection, whole-company precision guard.
- src/engine/navigator.ts and src/components/HierarchyNavigator.vue: collision-free keys and visible-label accessibility.
- src/components/EmployeeCard.vue: natural accessible name and separate ID description.
- src/components/ScenarioPlanner.vue: contrast and keyboard-focusable comparison region.
- src/style.css: contrast and comparison focus ring.

Tests/tooling/docs:

- src/engine/audit-regressions.test.ts (new); src/engine/scenario.test.ts (earlier precision rejection).
- scripts/reference_metrics.py, audit_math.ts, audit_performance.ts, audit_render.py, audit_browser.py, audit_production.py (new).
- package.json and package-lock.json: axe-core dev dependency.
- README.md and AUDIT_REPORT.md; data/audit/* raw evidence, fixtures, and screenshots.

The workspace is not a Git repository; this is a task change inventory rather than a commit diff. The temporary isolated install checkout was removed after verification. The original assessment PDF and synthetic product dataset were preserved.

Reproduction (from dayforce_OA; on PowerShell use npm.cmd if npm.ps1 is blocked):

```sh
npm ci
npm run lint
npm run typecheck
npm test
npm run build
npm exec tsx -- scripts/audit_math.ts
node --expose-gc --import tsx scripts/audit_performance.ts
```

With the dev server running, execute the existing check_explorer.py, check_analytics.py, check_scenario.py and audit_render.py. Browser tools require Python Playwright and installed Chromium. The performance script generates the extra dataset fixtures first.

For final production verification, run npm exec vite -- preview --host 127.0.0.1 --port 4173 --strictPort in a separate terminal. Then run audit_production.py and audit_browser.py with AUDIT_BASE_URL=http://127.0.0.1:4173/. README documents the commands and optional browser setup.

## 12. Final submission verdict

**NOT READY TO SUBMIT.** Local correctness, build, browser workflows, and the executed accessibility checks pass with no unresolved confirmed application P0/P1 issues. The mandatory public reviewer experience is not available, and original-data integration remains unverified.

To change the verdict: obtain the original CSV or an explicitly accepted schema substitute, rerun the independent/import checks on it, publish an accessible application with inspectable source as required by the PDF, and actually test those reviewer URLs. The completed non-deployment follow-up and remaining responsiveness/accessibility limitations are recorded below.


## 13. Non-deployment follow-up - 2026-10-23

**Result: confirmed import blocking, automatic-card readability and keyboard focus defects addressed; executed local checks pass.** Missing deployment/source URLs and inaccessible original CSV were explicitly excluded. The submission verdict is unchanged for those excluded reasons.

### Confirmed issues and limited changes

- **F01 / P2:** synchronous CSV read/parse/validation/build/aggregation occupied the UI thread. `App.vue` now sends the File/Blob to a Vite module worker. `processImport.ts` calls the existing `loadOrganization` unchanged. It returns batches of at most 500 employees/metrics or 1,000 reporting edges; the client assembles private Maps and publishes only the complete organization. Separating edge batches also bounds cloning for wide teams. Success, failure, replacement and unmount terminate workers. Validation errors preserve their issues; failure retains the prior dataset. No synchronous fallback was added.
- **F02 / P2:** initial desktop framing rendered 12px names at only **7.6-7.9 effective pixels** in 1280x720, 1280x800, 1440x768 and 1440x900 Chromium captures. Automatic framing now resets to native scale when fitting would go below 85%; all four sizes in all three engines open at 100% / **12px names / 220px cards**. Explicit Fit, density controls, geometry and existing pan/zoom remain available. Reports may be partially outside the canvas at native scale; this is the documented trade-off for readable automatic framing. No font, card, panel or layout redesign was made.
- **F03 / P2:** activating a search result with Enter removed the focused result and left `document.activeElement` on BODY. Keyboard selection now focuses the selected navigator row when that navigator is still visible. Closed mobile dialogs retain native focus restoration.

The hierarchy, metric, analytics and scenario calculation engines were not modified. No features, persistence, upload limits or scenario behavior were added. Worker execution is the only import-boundary architectural change requested here.

### Matched import benchmark

Evidence: [before](data/audit/followup/import-before.json), [final after](data/audit/followup/import-after.json), [harness](scripts/check_import_responsiveness.py). Same fixture hashes, Chromium 143, Windows/Node environment, 1440x900, no throttling, fresh pages, one warmup then five samples per size. The baseline was captured from the original production build before introducing the worker. The final after run used the final production bundle after other test workloads completed. Five-sample nearest-rank p95 equals the maximum and is a weak tail estimate. A separate concurrent exploratory run is retained as `import-after-concurrent-exploratory.json` and is excluded from this table.

Milliseconds, **median / p95**. Total = file-change capture through matching ready DOM and two animation frames. Maximum 10ms heartbeat interval measures UI-thread scheduling gaps during each import; it is not a parser-only duration or a guaranteed input-latency bound.

| Employees | Total before | Total after | Maximum timer gap before | Maximum timer gap after |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 108.9 / 109.4 | 125.8 / 155.3 | 92.9 / 94.0 | 90.5 / 118.7 |
| 10,000 | 148.0 / 154.7 | 193.3 / 206.1 | 132.8 / 137.4 | 95.1 / 111.5 |
| 40,000 | 347.7 / 403.3 | 466.0 / 481.3 | 327.0 / 387.0 | 110.2 / 128.5 |
| 100,000 | 601.1 / 826.1 | 823.4 / 922.3 | 579.5 / 805.7 | 166.7 / 199.0 |

At 40k the median maximum scheduling gap fell **66%** (327.0 -> 110.2ms); at 100k it fell **71%** (579.5 -> 166.7ms). Median maximum rAF gaps fell from 300.0 -> 100.0ms and 550.1 -> 116.6ms respectively. The real-worker browser check also navigated to Analytics while a 100k import was pending, retained the prior 40k dataset until completion, then showed 100k and preserved it after an invalid import, in all three engines.

This improves responsiveness rather than total speed: total medians increased from 347.7 -> 466.0ms at 40k and 601.1 -> 823.4ms at 100k because worker startup, serialization and result assembly add overhead. The worker eliminates synchronous CSV computation on the UI thread, **not every main-thread pause**. Remaining measured Long Tasks were 75-84ms at 40k and 73-77ms at 100k in the final run; assembly, Vue mounting and browser rendering still occur on the main thread. No zero-blocking claim is made. Memory peaks and worker/main overlap were not profiled; larger uncapped files remain a limitation. Engine timings shown in the footer are worker compute timings, excluding transfer/assembly/render time.

### Final verification and actual coverage

| Check | Actual result | Evidence |
| --- | --- | --- |
| Complete unit suite | **48 passed, 0 failed; 8 files** | [unit JSON](data/audit/followup/unit-results.json) |
| Lint / explicit TypeScript / production build | **PASS** | [recorded commands](data/audit/followup/final-checks.json) |
| Independent math rerun | 40k employees; 480k baseline comparisons and 600k scenario comparisons; **zero mismatches**, totals and baseline isolation preserved | [math results](data/audit/math-results.json) |
| Existing explorer / analytics / scenario workflows | **9/9 PASS**, three scripts x three engines | [suite results](data/audit/followup/cross-browser-suite.json) |
| Existing five-size production visual / axe / adversarial suite | **120 screenshots, 81 scans, zero reported axe violations, zero browser page errors**, three engines | [browser audit](data/audit/followup/final-browser/browser-audit.json) |
| Real 100k worker import / navigation / atomic replace / invalid retention | **PASS** in all three engines | [background import](data/audit/followup/background-import.json) |
| Short desktop / keyboard event checks | **PASS** in all three engines; 12 short-desktop screenshots | [keyboard/readability](data/audit/followup/keyboard-readability-after.json) |

Seven new worker tests cover serialized forest/order/decimal parity; all 40k employees, children, roots and metric parity; bounded wide-team messages; validation errors; pre-aborted requests; termination/late-result isolation; and startup/runtime/message/incomplete-result failures. Existing independent mathematical checks also passed again. The synthetic product CSV hash is unchanged.

The first async-browser run exposed old harness assumptions: explorer and scenario fixtures were searched before import completion. The scripts now explicitly wait for the imported filename; invalid-file loops wait for import controls to re-enable. Assertions were retained. `cross-browser-initial.json` preserves the failed timing runs; these are not counted as final passes. A Node test used unavailable `ErrorEvent`; its fake event was corrected. The targeted keyboard harness also needed to wait for responsive dialog mode and account for virtualized rows and native browser-chrome focus boundaries; no product changes were made for those harness assumptions.

Keyboard verification used real Playwright Tab, Shift+Tab, Enter, Space, arrows, Home, End and Escape events, rather than DOM click substitution: search-result focus, tree roving navigation/selection, canvas pan/Home, keyboard zoom, native-dialog Tab traversal, Escape and trigger-focus restoration. Existing suites additionally exercise keyboard scenario-table horizontal scrolling. Native dialogs can move focus through browser chrome/BODY at a Tab boundary; checks allow that but reject focus entering background page controls. This is an automated approximation of manual keyboard use, **not a human screen-reader or physical-device session**.

Visual inspection included before/after Chromium 1280x720, final Firefox 1440x768 and WebKit mobile populated planner captures. All five viewport audit states assert no document-level horizontal overflow. Explicit Fit still deliberately produces smaller cards; native-scale framing clips some branches inside the pan area. There was no formal target-size audit. Axe incomplete checks and lack of screen-reader/touch testing remain limitations.

### Files and reproduction

Production changes: `src/App.vue`, `src/services/importOrganization.ts`, `src/workers/importProtocol.ts`, `src/workers/processImport.ts`, `src/workers/import.worker.ts`, `src/components/OrgCanvas.vue`, `src/components/OrganizationExplorer.vue`, `src/components/HierarchyNavigator.vue`. Existing calculation engines are unchanged.

Tests/docs: `src/services/importOrganization.test.ts`; parameterized existing `check_explorer.py`, `check_analytics.py`, `check_scenario.py`, `audit_browser.py`; new `check_import_responsiveness.py`, `run_browser_suite.py`, `check_followup.py`, `check_background_import.py`; README and this report. Raw outputs are in `data/audit/followup/`. No package dependency changes in this follow-up.

With the production preview on 4173 and browser binaries installed, run the existing full suite via `python scripts/run_browser_suite.py`. Run `check_background_import.py` and set `QA_STAGE=after` for `check_followup.py`. Set `AUDIT_BASE_URL=http://127.0.0.1:4173/` and `QA_OUTPUT_DIR=data/audit/followup/final-browser` for `audit_browser.py`. Run the import benchmark alone; its default stage writes `import-after.json`. The original before artifact is preserved and requires the original build to reproduce. Standard npm and independent math commands remain in section 11.


## 14. Blue and slate palette - 2026-10-23

Applied the requested blue and slate palette across the explorer, analytics,
scenario planner and landing screen. Blue replaces teal accents in buttons,
selected states, chart bars and focus rings; slate replaces green-tinted neutral
surfaces, borders and text. Reporting connectors use slate. Status warning/error
colors retain their meaning. Layout, behavior and calculation code are unchanged.

Validation: production build and TypeScript passed. Chromium desktop (1440x900)
and mobile (390x844) checks covered all three populated views: six axe scans,
zero reported violations, zero browser errors and no document horizontal overflow.
The desktop explorer screenshot was visually inspected. Evidence:
[palette checks](data/audit/blue-slate/checks.json) and screenshots in that folder.
The earlier three-browser full suite predates this color-only change; it was not
repeated. Existing accessibility testing limitations still apply.


## 15. Dayforce-inspired styling - 2026-10-23

Supersedes the generic palette in section 14. Inspected the rendered public
[Dayforce homepage](https://www.dayforce.com/) and its computed styles. Reference
colors include primary blue #3067db, dark navy #08142d, button navy #10285b and
#183c88. OrgScope now uses these shades with white surfaces, pale blue fills,
turquoise accents, 8px button corners, bolder headings/navigation and a blue
welcome panel with an abstract turquoise accent. The OrgScope identity is retained.
Local Arial/Trebuchet font stacks approximate the reference typography; Dayforce's
Clarika fonts and branded assets were not imported. Workspace geometry,
controls, calculations and features are unchanged.

Validation: build (including TypeScript), lint and all 48 unit tests passed.
Chromium, Firefox and WebKit each covered welcome, explorer, analytics and a
populated planner at 1440x900 and 390x844: 24 screenshots and axe scans,
zero reported violations, zero page errors and no document horizontal overflow.
Desktop welcome/explorer screenshots were visually inspected. This is targeted
styling verification, not a repeat of the full interaction audit in section 13.
Evidence: [style checks](data/audit/dayforce-style/checks.json), reference screenshot,
computed reference styles and final captures under `data/audit/dayforce-style/`.


## 16. P1 employee-card selection reliability - 2026-10-23

**RESOLVED for the reproduced issue:** all specified card surfaces and workflows
pass with a single real pointer click in Chromium, Firefox and WebKit. No
repeated-click workaround, retry, debounce or selection delay was introduced.
The excluded deployment/original-data blockers remain unchanged.

### Confirmed root cause and reproduction

`EmployeeCard.vue` emitted selection only from `.employee-card-main`, the native
name/title button in the upper portion of each card. The surrounding article,
stats row, padding and empty footer area had no selection handler. A click in
those areas reached the card DOM but never invoked selection. This presented as
intermittence because users naturally clicked different areas of the same card,
particularly near boundaries at fractional zoom.

Reproduce on the original build: load Giga Corp, click Sam Lopez's name area,
then Riley Davis's stats row or unused footer space. Riley's pointerdown,
pointerup and click arrive at the correct `data-card="GC000002"`, but Sam remains
selected in the chart, inspector and navigator. Repeat Jamie/Drew/Sam/Riley,
including around 47% zoom. Native name/title-button clicks work; non-control
body clicks fail. The automated baseline independently reproduced this on all
three browser engines.

Capture-phase instrumentation recorded pointerdown/move/up, click,
got/lostpointercapture, target classes, employee IDs and coordinates; a mutation
observer recorded highlighted cards, inspector ID/heading and navigator selection.
For example, clicking Sam's `.employee-card-stats` reached its DIV with
`dragging=false` while Cameron remained selected, with no subsequent selection
update. Name-button clicks produced the expected selection/inspector mutation.
This establishes a missing event handler, rather than a selection update that
was subsequently overwritten.

Investigation also checked connector SVG hit-testing (`pointer-events:none`),
canvas overlays, transformed coordinates, event bubbling, drag handling,
selection refs/watchers and layout caching. No connector/overlay interception or
state overwrite was observed for this reproduction. Canvas panning already
excludes any target inside an article; it captures background pointers and pans
immediately without a movement threshold. That behavior was preserved. Existing
card transitions affect only border color/shadow, not card geometry.

### Smallest fix and files changed

- **Production: `src/components/EmployeeCard.vue` only.** Add a delegated article
  click handler that emits the existing `select` event for non-button surfaces.
  Main-button clicks keep their existing native selection action; footer buttons
  keep Expand/Collapse, pagination or Focus without a second/unrelated selection.
  The parent continues selecting by unique employee ID through the existing path.
- **Regression: `scripts/check_card_selection.py`**, plus this report and evidence
  under `data/audit/card-selection/`. No CSS, layout, pan/zoom, timing, worker,
  hierarchy or calculation-engine changes were made for this fix.

### Before/after browser results

All clicks use Playwright mouse or locator pointer events, with actual rendered
coordinates and `elementFromPoint` hit checks. No direct component method calls
or DOM-dispatched clicks are used. Assertions observe the normal Vue update and
two animation frames; they never repeat input or insert a workaround delay.

| Browser | Original core assertions | Original failures | Fixed assertions | Fixed failures |
| --- | ---: | ---: | ---: | ---: |
| chromium 143.0.7499.4 | 360 | 224 | 398 | 0 |
| firefox 144.0.2 | 360 | 172 | 398 | 0 |
| webkit 26.0 | 360 | 236 | 398 | 0 |

Original: **632 failed selection assertions out of 1,080**. Fixed: **1,194/1,194
passed**, including the original 360-case core plus 38 additional assertions per
browser for partially clipped default-camera cards, minor pointer jitter and
duplicate-name alternation. Before/after counts deliberately differ because the
additional checks were added after the core baseline was recorded.

The core covers all five initially visible employees across name/title, center,
stats, right-side whitespace and empty-footer surfaces; 32 rapid alternating
selections per phase; native scale, approximately 47% (eight control-wheel steps),
explicit Fit and the shorter 1440x900 desktop viewport. It repeats after empty
canvas clicks, panning and expand/collapse. Every selection checks unique ID,
pressed state, the sole highlighted card, exact inspector heading plus inspector
ID, and the navigator's selected ID. Names alone never determine success.

Additional assertions verify:

- Card clicks and a small ordinary pointer movement do not pan, zoom or recompute
  layout; intentional background drags still pan and preserve selection.
- Clicking empty canvas preserves selection and does not impair the next click.
- Expand/Collapse controls preserve an unrelated selected employee; pagination
  changes the intended page and keeps selection consistent with existing rules.
- Focus enters Riley's team; all newly visible team cards select correctly, as do
  cards on the second root report page.
- Enter/Space on native card selection buttons and Enter in the navigator retain
  correct ID selection and inspector synchronization.
- A fixture with two employees both named `Same Name` alternates correctly by ID
  for 32 clicks, including non-button surfaces.
- Every initially visible card in the actual 1440x900 native camera is selectable
  at an exposed point even when a card is partially clipped by the canvas.

A preliminary WebKit harness run exposed fractional-coordinate rounding: a
floating-point hit probe reported whitespace while the actual rounded mouse
coordinate landed on a pagination button. The regression now probes the same
integer coordinate it clicks and uses an unambiguous whitespace point. The
harness diagnostic is retained; it was not treated as an additional product
bug. No production coordinate conversion or drag behavior was changed.

### Final verification and evidence

- Complete unit suite: **48 passed, 0 failed**, eight files.
- Explicit TypeScript, ESLint and production build: **PASS**, all exit 0.
- Existing Organization Explorer Playwright suite: **PASS in all three engines**.
- New pointer selection regression: **398 assertions per engine, zero failures
  and zero page errors** in Chromium 143.0.7499.4, Firefox 144.0.2 and WebKit 26.0.

Evidence: [root cause](data/audit/card-selection/root-cause-evidence.json),
[original failures](data/audit/card-selection/before-results.json),
[fixed results](data/audit/card-selection/after-results.json),
[existing Explorer results](data/audit/card-selection/existing-explorer.json),
[unit results](data/audit/card-selection/unit-results.json),
[recorded checks](data/audit/card-selection/final-checks.json).
Per-engine `before-*-trace.json` and `after-*-trace.json` retain the event and
selection/inspector timelines. Tests cover the documented desktop workflows and
a duplicate-name fixture; they are not a claim of exhaustive clicking of all
40,000 employees, physical touch-device testing or screen-reader certification.

Reproduce against the built production preview at port 4173 with
`python scripts/check_card_selection.py` (defaults to all three installed engines).
`QA_STAGE=before` writes a separate original-build baseline; it must target the
original build. `QA_BROWSERS` optionally narrows engines, and `AUDIT_BASE_URL`
changes the preview URL. The original core fails without the card handler and
passes with it. Existing Explorer scripts accept `QA_BROWSER` and
`AUDIT_BASE_URL` as documented previously.


## 17. Staff engineer code-quality review - 2026-10-23

See [CODE_QUALITY_REVIEW.md](CODE_QUALITY_REVIEW.md) for the complete architecture,
type safety, Vue, algorithms, security, worker lifecycle, testing and documentation
review. **Code-review verdict: REVIEW READY WITH MINOR ISSUES.** This is distinct
from the submission verdict above; deployment and original CSV access were excluded.

Confirmed and fixed: analytics kept an obsolete branch page and query when an
import replaced the organization without changing null scope. The new three-engine
regression failed before (zero branch rows, two expected) and passes after. The
only production-code edit is the organization-identity dependency in its existing
state-reset watcher. No calculation, worker protocol, layout or interaction rewrite
was made. All engine file hashes remain unchanged.

Vitest's development chain was upgraded from 3.2.7 to compatible 4.1.12 to remove
confirmed advisories. Runtime/build dependencies are unchanged; npm audit now
reports zero affected packages. Two additional worker tests cover partial-result
failure and cancellation isolation. README now describes the current architecture,
setup, metrics, tests and limits without contradictory historical suite counts.

Final verification: lint, explicit TypeScript, build and canonical **50 tests in
eight files** pass; all nine existing browser workflows and all **1,194 pointer
selection assertions** pass in Chromium/Firefox/WebKit. Real worker import/race,
analytics replacement and keyboard checks also pass. Independent math again has
zero mismatches over 480,000 baseline and 600,000 scenario comparisons. A clean
isolated npm ci, 50 tests and build passed; its temporary checkout was removed.

Sequential timing drift was investigated rather than accepted as a code regression.
A comparison build reproduced the original JavaScript asset exactly, then alternated
original/revised pages in one browser. At 40k the import median was 477.2/475.5ms
before/after; at 100k 914.0/958.6ms (about 4.9% slower after, with overlapping/noisy
samples). No speed improvement is claimed. Full raw timing, memory observations,
method limits and the initial less favorable sequential results are retained in
the review. Main-thread rendering pauses, peak worker/UI memory and weak tail
estimates remain limitations.

Evidence: [final commands](data/code-quality/final/checks.json),
[canonical unit results](data/code-quality/final/unit-results.json),
[workflow results](data/code-quality/final/cross-browser-suite.json),
[selection results](data/code-quality/final/card-selection.json),
[paired timings](data/code-quality/paired-import-performance.json).
The temporary clean-install copy initially caused duplicate test discovery in one
workspace run; it was removed and the canonical 50-test run repeated. That duplicate
100-test artifact is not counted as additional coverage. The full visual/axe audit
was not repeated for this nonvisual change; earlier executed coverage remains dated.


## 18. Simplified footer and Git preparation - 2026-10-23

The UI footer now shows dataset name and currency only. Parse/build/aggregate
milliseconds were developer diagnostics rather than information needed for user
decisions; underlying timings and benchmark/audit outputs are retained. Production
build (including TypeScript) passed, and a Chromium smoke check verified Costs in
CAD is shown without Parse timings. No calculation changes were made.

At the user's request, initialized Git and created the private destination
[nati5174/OrgScope](https://github.com/nati5174/OrgScope). The source upload is
pending explicit confirmation after automatic approval review rejected export of
the staged project, including assessment PDF and audit evidence, to an inferred
destination. No successful source push is claimed. Earlier statements that this
workspace was not a Git repository describe the earlier audit state.

Dependencies, primary build output, local environment files and Python caches
are ignored. Git preserves audited file bytes; the staged synthetic CSV matches
its documented SHA-256. Hosted application delivery remains out of scope here.


Git publication scope confirmed: the user authorized app code and synthetic data
only, excluding the assessment PDF and raw audit evidence. Those files are now
ignored and removed from the initial Git index, while remaining intact locally.
The source package retains project documentation and synthetic-summary fixtures.
Historical raw-evidence links in reports refer to local-only artifacts, as explained
in README. The private destination is https://github.com/nati5174/OrgScope.
