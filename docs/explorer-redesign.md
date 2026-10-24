# Organization explorer redesign

## Problem and resulting behavior

The previous chart used `x = depth * 300` and a separate `y = row * 250`
counter for each depth. It never arranged parents from their children, so curved
links crossed unrelated row positions. Oversized cards displayed salary metrics
that were also in the inspector. Focus/search discarded expansion state.

The replacement arranges the visible hierarchy with a tidy-tree algorithm,
uses 220×112px cards, and routes orthogonal connectors between columns. Salary
metrics are grouped in the inspector. The navigator and chart share selection
and expansions; focusing narrows visualization scope without changing metrics.
The chart is still the primary view.

## Components and state

| Source | Responsibility |
| --- | --- |
| `src/composables/useExplorer.ts` | Selection, focus, expansion, pagination, density; no salary calculations |
| `src/engine/treeLayout.ts` | D3 tidy-tree positioning and orthogonal connector geometry |
| `src/engine/navigator.ts` | Iterative navigation projection and ancestor/page reveal |
| `OrganizationExplorer.vue` | Coordinates the three panels, breadcrumbs, focus/back actions |
| `OrgCanvas.vue` | Visible layout, independent camera, fit/zoom/pan and keyboard controls |
| `EmployeeCard.vue` | Compact selection/expansion/report page controls |
| `HierarchyNavigator.vue` | Search and virtualized tree with keyboard navigation |
| `EmployeeDetails.vue` | Grouped identity, reporting, salary, and descendant-only costs |
| `ExplorerPanel.vue` | Desktop panel or accessible native modal drawer |

The original CSV parser, hierarchy construction, aggregate metrics, analytics
engine, and scenario engine are retained. `visibleNodes` adds an optional page
size argument while preserving its previous default and existing unit tests.
Existing public explorer props/events still support scenario previews and
analytics navigation. Each explorer instance has isolated navigation/camera
state; generated input IDs avoid collisions when a scenario chart is mounted.

Camera changes never rebuild the layout. Selection of an already-visible
employee reuses the projection and layout; browser tests check the layout
revision. Only expansion, paging, scope, or density changes alter geometry.
Observers and event listeners are disconnected on unmount.

## Trade-offs

- Four reports per page is the default to keep cards readable. Eight or 24
  can be selected deliberately. All reports remain reachable through paging,
  search, and focus. Counts and salary totals always include full subtrees.
- The chart has a strict 150-card limit. A focus action is preferable to a
  diagram of thousands of employees. A limit message explains the boundary.
- The left tree already supplies compact list navigation; an additional
  Tree Explorer tab would duplicate that experience.
- Navigation flattening is proportional to expanded/paged rows; DOM rendering
  is virtualized. A fully revealed deep path can be O(n) to prepare, while
  a typical path reveal is proportional to depth and ancestor reporting spans.
- On mobile the root stays readable rather than forcing every card into a
  tiny fit scale. Out-of-view branches can be reached with touch pan, explicit
  Fit to view, or the navigator. The desktop panels become modal surfaces.
- No ELK, backend, or worker was introduced. D3 hierarchy directly addresses
  the observed geometry problem; measured layout work is small.

## Verification

Commands executed successfully for this revision:

```sh
npm run lint
npm test
npm run build
npm run benchmark:explorer
python scripts/check_explorer.py
python scripts/check_analytics.py
python scripts/check_scenario.py
```

The build includes `vue-tsc --noEmit`. The suite has 37 tests, including the
existing hierarchy/analytics/scenario tests and new layout/state/navigation
coverage. Geometry tests assert cards do not overlap and connector segments
do not enter card interiors. Collapse reproduces the original compact bounds.

Chromium checks include desktop 1440×1000, tablet 1024×900, and mobile 390×844;
initial root, expand/collapse, all 24 reports, deep search, navigator/chart/
inspector synchronization, keyboard tree operation, focus/back/breadcrumbs,
preserved expansion, density changes, fit, zoom, pointer and keyboard pan,
drawers and Escape, 150-card cap, no page overflow, and a 40k-level navigation
path with a virtualized DOM. Analytics and scenario smoke checks also pass.
These checks do not replace a complete accessibility audit or testing on
physical touch devices.

## Screenshots and performance

- [Before desktop](../data/redesign/before-desktop.png)
- [After desktop](../data/redesign/after-desktop.png)
- [Before mobile](../data/redesign/before-mobile.png)
- [After tablet](../data/redesign/after-tablet.png)
- [After mobile chart](../data/redesign/after-mobile-chart.png)
- [After mobile inspector](../data/redesign/after-mobile-inspector.png)

Measurements use **the generated synthetic 40,000-employee CSV**, not the
unavailable original assessment spreadsheet. Additional browser tests generate
a 40k-level chain specifically to test worst-case path navigation.

Node v22.11.0 / AMD Ryzen 5 PRO 7545U: ten runs after one warmup measured
0.183 ms median for a 150-card projection + D3 layout + connector generation,
and 12.8 ms median to flatten all 40,000 navigation rows. Each chart run averages
100 calculations. Parsing, file reading, and browser rendering are excluded.

Chromium 143 recorded three expand clicks at 13.5, 28.5, and 31 ms through two
requestAnimationFrame callbacks. This includes frame scheduling; it is not
a guaranteed paint-time measurement. Chart DOM was capped at 150 cards and
navigator DOM stayed below 40 rows in the tested viewports. Hardware, background
load, and browser settings affect results. Raw runs and methodology live in
`data/redesign/layout-benchmark-results.json` and `browser-results.json`.

All local assessment functionality remains available: CSV ingestion, expand/
collapse, descendants, non-leaf descendants, manager/IC/total descendant salary
costs and the documented cost ratio, responsive navigation, analytics, and
hypothetical scenario planning. Hosting/source publication remains a separate
submission step.
