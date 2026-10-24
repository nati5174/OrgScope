# OrgScope - Staff Engineer Code Quality and Architecture Review

Review date: 2026-10-23 (America/Toronto). Environment: Windows, Node 22.11.0,
AMD Ryzen 5 PRO 7545U; Chromium 143.0.7499.4, Firefox 144.0.2, WebKit 26.0.
Public deployment and inaccessible original CSV are excluded from this review.

## 1. Executive summary

**REVIEW READY WITH MINOR ISSUES.** The architecture is appropriately small and
cohesive for this assessment. Correctness-critical code is independent of Vue,
validated at CSV ingestion and supported by independent mathematical evidence.
No confirmed application P0/P1 issue remains from this review.

Made one targeted production-code correction: analytics now resets its page and
search on organization replacement, preventing an empty branch table after an
import. Updated only the development test runner for confirmed advisories, added
worker/race and analytics regression coverage, and replaced contradictory README
history with current reviewer documentation. No calculation, layout, styling,
identity, selection, worker-protocol or feature redesign was made.

Final checks: **50 tests across eight files**, lint, explicit TypeScript and build
pass; nine existing browser workflows pass; **1,194 pointer selection assertions**
pass across three engines; worker/import-race, analytics replacement and keyboard
checks pass. Independent math reports zero mismatches over 480,000 baseline and
600,000 scenario comparisons. Dependency audit now reports zero affected packages.
These are executed local checks, not an unrestricted production-readiness claim.

The original three-page assessment PDF was read directly using pdfplumber, plus
the README, AUDIT_REPORT and all 23 production TypeScript/Vue modules. No Git
repository exists; none was initialized. Existing source hashes and candidate-file
copies were recorded before edits. Initial checks and evidence are retained under
[data/code-quality/baseline](data/code-quality/baseline/).

## 2. Architecture assessment

| Boundary | Responsibility and assessment |
| --- | --- |
| `engine/organization.ts` | Domain types, Papa Parse validation, exact cent conversion, indexes, aggregation and search; no Vue dependency |
| `engine/analytics.ts`, `scenario.ts` | Pure scoped analytics and isolated hypothetical moves; reuse validated organization data |
| `engine/explorer.ts`, `navigator.ts`, `treeLayout.ts` | Projection, ancestor paths, flattened navigator rows and D3 layout; separate from salary logic |
| `workers/processImport.ts`, `import.worker.ts` | File reading and existing engine execution in a dedicated module worker |
| `services/importOrganization.ts` | Worker ownership, termination, abort handling, private index assembly and atomic result publication |
| `composables/useExplorer.ts` | Single selection/focus source, expansion/pages and cached chart projection |
| `components/` | Presentation and pointer/keyboard behavior; analytics/planner own their local UI state |
| `App.vue` | Organization ownership in a shallow ref, latest-import guard, dataset generations and local view navigation |

The [relative import graph](data/code-quality/static-review.json) contains no
circular dependencies. The graph is a static local-import check, not a complete
bundler/security analysis. UI-to-engine dependencies are one-way; the worker
shares the engine rather than duplicating aggregation. Domain types living beside
the organization constructor are cohesive; a new `types/` directory is unnecessary.

State ownership is clear: imports atomically replace a dataset; generations reset
Explorer/Planner state. Explorer emits IDs through a controlled parent selection
path. Analytics owns scope-local paging/query state; its missing dataset reset was
the one production correction. `v-show` retains appropriate Explorer/Planner
state across ordinary view switches, while Analytics is mounted for its active
view. No global state library or new application layer is justified.

TypeScript strict mode is enabled, component props/emits are typed, and worker
messages form a discriminated union. No explicit production `any` type was found.
Most non-null assertions follow the constructor's invariant that every employee
has children/metrics entries and all managers exist in an acyclic graph. The
worker's DOM/worker scope assertion bridges TypeScript lib contexts; it does not
validate CSV. Full runtime schema validation of private, same-build worker messages
would duplicate trusted engine work; no protocol rewrite was justified.

## 3. Findings

| ID / severity | File and location | Problem and significance | Improvement / risk / resolution |
| --- | --- | --- | --- |
| CQ01 / P1 | `src/components/WorkforceAnalytics.vue:11` | The scope-only watcher omitted organization identity. Importing a smaller dataset from branch page 2 leaves zero rows despite valid branches; old query remains. Confirmed in all three engines. | Watch organization and scope together; reset only local page/query. Low risk, O(1), identity-only watch. **Fixed**, regression fails before and passes after. |
| CQ02 / P1 maintenance | `package.json:38`, lockfile | Audit identified three affected dev packages: Vitest, mocker and tinypool, with two critical and one moderate package labels. These are not three independently proven application exploits. | Security-motivated Vitest 3.2.7 -> 4.1.12, exact version; compatible with existing Node/Vite. Moderate test-tool migration risk, mitigated by all tests and isolated clean install. **Fixed**, audit zero. Runtime/build dependency versions unchanged. |
| CQ03 / P2 | Original `README.md:1`, old phase/test-count sections | README claimed complete-suite counts of 24, 30 and 37 in different places, mixed phase history with current instructions and scattered worker limitations. Misleads reviewers. | Replace with current setup, features, architecture, metrics, checks and realistic limitations. Documentation-only risk. **Fixed**. |
| CQ04 / P2 | `src/services/importOrganization.test.ts:63`, `:77`; new browser regressions | Existing tests covered errors and abort, but not failure after receiving valid partial chunks or a replacement racing a partly received import. App-level rapid-import behavior needed direct coverage. | Two additional unit cases and real-worker overlap checks; no worker production changes. Low risk. **Covered**, including latest-valid wins, latest-invalid preserves prior data and exact termination counts. |
| CQ05 / P3 | `WorkforceAnalytics.vue`, `ScenarioPlanner.vue`, some other templates | Long template lines and compact multi-statement scripts are harder to review. This is readability debt, not a demonstrated runtime defect. | Gradual formatting when those blocks change; no repository-wide formatter or structural rewrite near submission. **Documented, deliberately unchanged**. |
| CQ06 / P2 existing limitation | Import result assembly, analytics/scenario UI paths | Main-thread index assembly/rendering still has pauses; scenario Map copies are O(n), uploads uncapped and worker/UI memory overlaps. | Keep measured limits explicit. No evidence justifies a new cache, persistent-map library or streaming protocol during a maintenance review. **Documented**, not represented as solved. |

CQ02 threat assessment: the
[Vitest mocker advisory](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9)
concerns exposed mock-registration plugins; this project uses local `vitest run`
and does not configure those plugins. The
[tinypool worker-options advisory](https://github.com/tinylibs/tinypool/security/advisories/GHSA-5gmw-xhrv-c9v3)
requires a prototype-pollution prerequisite. No such frontend-to-Node exploit path
was identified here. Nevertheless, removing the affected development chain is a
compelling, bounded dependency-maintenance change. Vitest 4.1.12 patches mocker
and removes the prior tinypool dependency. The raw
[before audit](data/code-quality/dependency-audit.json) and
[after audit](data/code-quality/final/dependency-audit.json) retain exact findings.

Security review also found: employee content is rendered through Vue text/attribute
bindings, no `v-html`, dynamic code execution or employee-controlled navigation
URLs; IDs use Maps and escaped navigator selectors. CSV validation rejects malformed
identities/relationships/salaries before publication. Export creates a JSON Blob
and revokes its URL. No secrets or secret files were identified in reviewed source
and project configuration; this was not a forensic scan of the entire workspace.
Zero audit findings do not establish general exploit freedom.

## 4. Changes implemented

- `src/components/WorkforceAnalytics.vue`: one watcher dependency addition and an
  invariant comment. Invalid replacements still preserve the prior UI state.
- `package.json`, `package-lock.json`: only Vitest's development chain upgraded.
  Vue 3.5.44, Papa Parse 5.7.0, d3-hierarchy 3.1.2, Vite 6.4.5, Vue plugin 5.2.4
  and Tailwind Vite plugin 4.3.3 remain at their baseline versions.
- `src/services/importOrganization.test.ts`: two partial-result/cancellation tests.
  All original test names remain present; no existing assertions were weakened.
- `scripts/check_analytics_replacement.py`: 12-root forest page 2 -> smaller
  replacement, query reset, totals and failed-import retention in all engines.
- `scripts/check_import_races.py`: real native workers with termination counters;
  overlapping 100k/tiny imports and newest-invalid retention, without inserted delays.
- `README.md`: concise current reviewer documentation. This report and the audit
  cross-reference record the review; evidence is under `data/code-quality/`.

[Change inventory](data/code-quality/change-inventory.json) compares baseline
hashes. All `src/engine/` source/test hashes are unchanged. No production worker,
Explorer, canvas, card, style or scenario file changed during this review.
The original card-selection fix remains intact; both baseline and final stress
runs pass 398 assertions per engine.

## 5. Changes deliberately avoided

No Pinia/store, branded ID framework, generic repository layer, new chart library,
`types/` reorganization or new dependency for formatting was added. Most prop paths
are short and express clear ownership. Sharing validated domain types is appropriate.

Did not rewrite proven aggregation/scenario math, change ratio definitions, replace
Maps with a persistent collection, add per-employee analytics caches, add defensive
fallbacks for impossible internal Map states or validate the entire worker payload
again on the UI thread. Those changes carry correctness or performance risk without
an observed problem. Readonly public views of Maps could strengthen future type
contracts, but converting all interfaces now would be a broad cosmetic change.

Did not modify pan thresholds, click propagation, SVG layers, transitions, zoom,
layout or selection: source inspection and 1,194 real-pointer assertions establish
that the previously fixed defect is absent in this baseline and final build.
Did not alter unsupported ESLint's major version merely to remove a warning;
current lint passes and its dependencies have no reported audit findings.

## 6. Algorithmic complexity and numerical integrity

Let L be CSV text size, n employees, h ancestor-path height, s scoped employees,
b reporting branches, v projected cards (capped at 150) and r flattened navigator
rows (at most n).

| Operation | Expected time / memory | Trade-off |
| --- | --- | --- |
| CSV parse/validation | O(L); O(L+n) retained parsing data | Exact BigInt cent conversion, no arbitrary file cap |
| Indexes and leaf-to-root aggregates | O(n) time, O(n) memory | Iterative queue; processed-node count detects disconnected cycles |
| Employee/metric lookup | Expected O(1) | Validated Maps; selected employee excluded from descendant metrics |
| Search | O(n) record scan, plus string normalization; result cap 30 (20 in pickers) | Early exit on enough matches; no large search index |
| Select/reveal/depth | O(h + sibling scans); may scan O(r) to reveal a navigator row | Lookup itself is O(1), but complete selection is not universally O(1) |
| Chart projection / D3 layout | O(v) for bounded page size, O(v) memory | Only the projected tree reaches D3; no 40k-card DOM |
| Navigator flatten | O(r) time/memory when expansion/pages change | Virtual DOM rows are bounded by viewport/overscan, not flattened-data size |
| Analytics | O(s + b log b) time, O(s+b) memory | Scoped traversal and sorted branches; computed reuse until org/scope changes |
| Scenario | O(n+h) overall, including parent report-array copies; O(n+h) space | Index copies O(n), metric deltas O(h); original records shared immutably |
| Worker import | O(L+n) computation/transfer/index assembly | Compute off UI thread; private O(n) main indexes coexist with worker data |

Salary strings convert to exact integer cents before Number bounds checks.
Nonnegative individual and whole-company totals are safe integers. Invalid CSV
never replaces valid state. Manager status derives from actual reports;
management + IC salary equals total descendant cost. Scenario copies only changed
records/ancestor metrics, validates cycles/no-op moves and reconciles final totals.
Analytics intentionally includes its leader, and separately labels cost/headcount
ratios. No definitions changed. Unit tests and the independent Decimal oracle
support these conclusions; tests do not make the invariants mathematically universal.

## 7. Test results and verification

| Check | Baseline | Final | Evidence |
| --- | --- | --- | --- |
| ESLint, explicit TypeScript, build | All exit 0 | All exit 0 | [baseline commands](data/code-quality/baseline/checks.json), [final commands](data/code-quality/final/checks.json) |
| Full Vitest suite | 48 tests, 8 files, no failures | **50 tests, 8 files, no failures** | [baseline unit](data/code-quality/baseline/unit-results.json), [canonical final unit](data/code-quality/final/unit-results.json) |
| Existing Explorer / Analytics / Scenario Playwright | 9/9 pass | 9/9 pass | [final workflows](data/code-quality/final/cross-browser-suite.json) |
| Employee pointer reliability | 398 per engine, 1,194 total pass | 398 per engine, 1,194 total pass | [final selection](data/code-quality/final/card-selection.json) |
| 100k real background import / navigation / invalid retention | All engines pass | All engines pass | [background import](data/code-quality/final/background-import.json) |
| New analytics replacement regression | **Fails in all engines**, zero rows/two expected and stale query | Pass in all engines; correct rows, query, salary totals and invalid-file retention | [before](data/code-quality/baseline/analytics-replacement.json), [after](data/code-quality/final/analytics-replacement.json) |
| Real-worker overlapping imports | New coverage | All engines pass; five workers terminate once each per run | [race results](data/code-quality/final/import-races.json) |
| Keyboard / short-desktop checks | Existing prior audit | All three engines pass | [keyboard/readability](data/code-quality/final/keyboard-readability.json) |
| Independent hierarchy / scenario oracle | Prior audit retained | 40k employees, 480k + 600k comparisons, zero mismatches | [math](data/code-quality/final/math-results.json) |
| Isolated clean install | Not repeated before edits | npm ci, 50 tests and build exit 0; temporary checkout removed | [clean install](data/code-quality/final/clean-install.json) |
| npm audit | 3 affected development packages | 0 affected packages | Before/after audit links in section 3 |

Commands executed: `npm run lint`, `npm run typecheck`, `npm test` (also JSON
reporting), `npm run build`, `npm audit --json`, `npm exec tsx -- scripts/audit_math.ts`,
`python scripts/run_browser_suite.py`, `check_background_import.py`,
`check_import_races.py`, `check_analytics_replacement.py`, `check_followup.py`
(with QA_STAGE=after), and `check_card_selection.py`. Isolated install used
`npm ci`, `npm test` and `npm run build` against copied source/fixtures.

A temporary clean-install source copy initially overlapped the workspace Vitest
run and was discovered as a second set of tests. It was removed and the canonical
suite rerun: exactly 50 tests in eight files. The superseded double-discovery JSON
is retained separately, not counted as 100 independent tests. The
[canonical rerun record](data/code-quality/final/canonical-unit-check.json) explains
this harness correction. Windows transient file locks required a second cleanup
attempt; final evidence confirms removal. No product assertions were relaxed.

The full visual/axe audit was not repeated because no layout/style change was
made. Existing browser keyboard/geometry and all interaction suites were rerun.
This review does not claim a human screen-reader or physical-device session.

## 8. Performance comparison

Measurements use the same hardware, Node 22.11, synthetic fixtures, original
production preview at 4173 and recorded source hashes. The initial baseline and
final benchmark commands ran separately from test workloads, with existing audit
warmup/sample methods. Raw results are retained even when noisy.

**Sequential comparison raised a concern:** at 40k, total import median changed
281.6 -> 422.4ms; at 100k, 553.6 -> 796.0ms. Unchanged Node engine measurements
also varied, so those separate-time samples were not accepted as proof of a code
regression or ignored as an inconvenience.

Built a separate comparison bundle by substituting only the preserved original
analytics component through a Vite load hook. Its main JavaScript filename/hash
reproduces **`index-BL4d6ipg.js` exactly**, matching the original baseline, despite
the test-runner upgrade. Worker and CSS assets are unchanged. The final bundle
diff is the small analytics identity watcher. See
[comparison build](data/code-quality/comparison-build.json).

Then alternated original/final pages in one Chromium process, A/B then B/A,
one warmup per build/size and ten paired samples per build/size. Same fixture
hashes and heartbeat/rAF harness, no simultaneous test workload. Below is
**median / nearest-rank p95 milliseconds**; at ten samples p95 is the maximum,
not a reliable population tail estimate.

| Employees | Original total | Revised total | Original max timer gap | Revised max timer gap |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 141.8 / 200.0 | 117.2 / 202.7 | 101.5 / 158.0 | 84.1 / 139.4 |
| 10,000 | 198.2 / 222.4 | 198.6 / 237.8 | 94.2 / 107.2 | 94.9 / 115.0 |
| 40,000 | 477.2 / 515.7 | 475.5 / 565.6 | 128.9 / 161.2 | 121.7 / 162.0 |
| 100,000 | 914.0 / 1015.1 | 958.6 / 1134.9 | 178.6 / 253.4 | 175.8 / 218.3 |

The 40k median is effectively unchanged (-0.3%). At 100k the revised total median
is 4.9% slower; heartbeat-gap median is slightly lower. Raw samples overlap and
maximums are noisy; this is not evidence of a speed improvement or zero overhead.
The byte-identical original build now also measures much slower than the first
baseline, demonstrating environment/time drift. No substantial 40k regression
was established. The tiny constant-time watcher correction is accepted for its
confirmed correctness benefit; continued 100k tail profiling remains a limitation.
Do not interpret these samples as a responsiveness SLA.

Raw artifacts: [sequential baseline import](data/code-quality/baseline/import-performance.json),
[sequential final import](data/code-quality/final/import-performance.json),
[interleaved pairs](data/code-quality/paired-import-performance.json).
`data/code-quality/build-comparison.mjs` and `measure-paired.py` retain the exact
comparison procedure. The original bundle was served on local port 4174.

Existing Node audit: one warmup, ten runs per size, explicit GC; medians below.
Pure engine source and runtime dependency versions are unchanged. These timings
exclude browser/file transfer and were measured in separate processes, so changes
are observations, not attributed algorithmic speedups/regressions.

| Operation (ms) | 40k before | 40k after | 100k before | 100k after |
| --- | ---: | ---: | ---: | ---: |
| CSV parse | 122.59 | 175.02 | 326.10 | 318.00 |
| Build/index | 75.03 | 99.14 | 237.70 | 217.53 |
| Aggregate | 30.02 | 30.98 | 82.68 | 73.06 |
| Full-scan search | 8.42 | 9.14 | 12.82 | 13.67 |
| Analytics | 26.14 | 27.28 | 46.98 | 46.20 |
| Scenario | 30.77 | 37.96 | 116.66 | 88.10 |
| Bounded layout | 0.93 | 1.25 | 1.17 | 1.34 |

Sampled Node heap delta after load: 40,000: 55.2 -> 48.3 MiB; 100,000: 117.3 -> 117.9 MiB.
These are not peak memory or browser-worker memory measurements. No memory
improvement or leak-freedom claim is made. Three existing Chromium expand samples
had medians 22.2ms before and 21.4ms after through two animation frames; the sample
is too small for a tail claim. Chart <=150 cards, navigator <40 DOM rows, cached
selection layout, focus, search and scenario workflows remain verified by the
existing tests. Selection timings themselves were not separately benchmarked.

Raw [Node baseline](data/code-quality/baseline/engine-performance.json) and
[Node final](data/code-quality/final/engine-performance.json) include all four sizes,
individual runs and memory samples. The review adds no per-employee traversal or
cache to selection, search, scenario, layout or import. The analytics watcher
observes organization identity, not a deep traversal of 40k reactive records.

## 9. Remaining technical debt

- Dense templates and compact scripts could be reformatted gradually. Shared
  money formatting is small presentation duplication; extracting a utility is
  optional and should preserve per-view compact/precision choices.
- Readonly Map interfaces would better express scenario-sharing conventions;
  current producers honor immutability and regression tests cover isolation.
- Main-thread result assembly/rendering, synchronous scoped analytics/search,
  O(n) scenario Map copies, uncapped uploads and unmeasured peak worker/UI memory
  remain the meaningful scalability limits. No new data caps/features were added.
- UI/browser performance tails have small samples and visible environmental
  drift. No new long-duration memory soak or physical-device test was performed.
- Test scripts use generated fixtures and sometimes replace default evidence
  paths. This review explicitly copied baseline/final artifacts for isolation;
  a unified harness is a future tooling improvement, not a new architecture need.
- Clean npm ci still warns about unsupported ESLint 9.39.5 and unapproved esbuild
  install-script entries under the environment's npm policy. Install/build/tests
  succeed; dependencies report no audit findings. A lint-tool major upgrade is
  independent maintenance, outside the security-motivated Vitest change.

## 10. Final code-review verdict

**REVIEW READY WITH MINOR ISSUES.** The code demonstrates simple boundaries,
validated identities and money, iterative aggregation, sensible bounded rendering,
explicit ownership, real-pointer regressions and independent scenario/math checks.
All confirmed P1 findings from this review are addressed; no P0 issue was found.

The accepted changes solve one demonstrated state defect, remove a confirmed
advisory chain and improve verification/documentation without rewriting proven
logic. Remaining issues are documented readability/tooling and measured scaling
trade-offs. This verdict concerns the local engineering review, not delivery
approval; public deployment and original CSV availability remain out of scope.
