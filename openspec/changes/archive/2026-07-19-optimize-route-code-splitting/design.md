## Context

`apps/web/src/App.tsx` currently imports DashboardPage, five non-default page modules, and CommandPalette statically. Vite therefore emits one 247,182-byte production JavaScript file (74,538 bytes when gzipped), even though the default `/` route only renders Dashboard.

The page code is not the majority of this payload. An isolated bundle of the React 19 and ReactDOM startup path is approximately 193 KB raw and 60 KB gzip, while minifying the five non-default pages and their chart helper independently produces approximately 22 KB raw and 8 KB gzip. The goal is consequently to establish a scalable route boundary and obtain a modest measurable cold-start reduction, not to claim that vendor chunking eliminates the React runtime from first load.

Constraints:

- Preserve the current custom History API router, URLs, API calls, and page behavior.
- Keep Dashboard as the optimized default entry route.
- Keep AppShell visible during asynchronous route loading and failures.
- Reuse the existing Skeleton and feedback primitives.
- Do not add a routing library or bundle-analysis dependency.
- Keep this work independent from the active font-subsetting change.

## Goals / Non-Goals

**Goals:**

- Remove every non-default page module from the Dashboard initial static dependency graph.
- Keep Dashboard and CommandPalette immediately available after application startup.
- Provide accessible, layout-stable route loading feedback.
- Make lazy-module failures recoverable without losing global navigation.
- Give React runtime code a stable cache boundary for repeat visits.
- Measure the recursive initial graph rather than only the application entry filename.
- Establish enforceable initial and total JavaScript budgets.

**Non-Goals:**

- Replacing the custom router with React Router or another routing framework.
- Moving Dashboard into an asynchronous chunk.
- Lazy-loading CommandPalette, the shared API client, or small shared presentation primitives.
- Splitting the two lightweight SVG chart implementations into standalone chunks.
- Refactoring global CSS into route-owned stylesheets.
- Claiming a particular TTI, LCP, INP, or scrolling improvement from byte counts alone.
- Changing backend endpoints, frontend URLs, data-fetch timing, or visible page content.

## Decisions

### 1. Keep Dashboard eager and declare five lazy page components at module scope

Replace the five non-default page static imports with top-level `React.lazy` declarations backed by literal dynamic imports. Adapt the existing named page exports in the lazy loaders rather than changing every page's public export solely for this work.

DashboardPage remains a static import. This avoids adding an extra request and Suspense transition to the dominant `/` entry while accepting that a first-ever direct visit to another route also downloads Dashboard code.

Declare lazy components outside `App` so React caches each loader and component identity across renders. Continue to match paths in the existing `renderRoute` function; the lazy boundary changes module delivery, not routing semantics.

Alternatives considered:

- **Lazy-load every page, including Dashboard:** improves direct deep-link payloads but makes the primary route wait on a second request.
- **Group pages into feature chunks:** saves a few requests but makes list routes download detail code and introduces facade modules or manual grouping for very small chunks.
- **Add React Router:** provides richer data-router features but is unnecessary for six stable routes and increases scope and payload.

### 2. Keep CommandPalette in the initial graph

CommandPalette and its filter logic account for only about 7.6 KB raw and 2.9 KB gzip when independently minified. It is also a global keyboard-driven interaction with no hover target that can reliably preload it before first use. Retaining it avoids first-shortcut network latency and keeps its existing focus behavior unchanged.

Use direct component imports in the touched application entry where practical so the local `components/index.ts` barrel does not make the route graph harder to inspect. This is a dependency-clarity change only; unrelated page imports are not refactored.

Alternative considered:

- **Conditionally lazy-load CommandPalette:** saves a small amount on the cold Dashboard path but makes the first `Cmd+K`, `Ctrl+K`, or `/` interaction depend on a chunk request.

### 3. Put a single route Suspense boundary inside AppShell

AppShell remains outside the asynchronous boundary. Its `children` area receives:

1. a route-scoped ErrorBoundary keyed by the current path;
2. a Suspense boundary;
3. the selected route element.

The Suspense fallback is a small `RouteLoadingFallback` composition built from the existing Skeleton primitive. It includes a `role="status"` with the accessible name `Loading page`; decorative Skeleton elements remain `aria-hidden`.

Suspense covers code loading only. Existing page-level loading states continue to represent API requests made from effects, so a route may briefly progress from the route Skeleton to its existing data-loading surface.

Alternatives considered:

- **Boundary around the entire AppShell:** would hide navigation during loading and remove the user's escape path after a failure.
- **Separate boundary in every route branch:** duplicates fallback and error wiring without providing independent concurrent regions.
- **Keep the old page visible during loading:** avoids a fallback flash but makes the URL and active navigation identify a new route while stale content remains visible.

### 4. Make lazy import errors route-scoped and recoverable

Extend the existing ErrorBoundary contract only as much as needed to render a route-load failure fallback with a page reload action. Keying the route boundary by the full path remounts it when the user navigates, including between detail ids, so an error on one module or route does not poison later navigation.

The reload action performs a normal document reload, allowing Vite's latest HTML and content hashes to be fetched after a deployment invalidates an old chunk URL. AppShell stays outside the boundary, so navigation is still available even if reload is not appropriate.

Automatic reload through `vite:preloadError` is deliberately excluded. Without a guarded retry policy it can create reload loops for persistent network or server failures.

### 5. Create a targeted React vendor cache boundary

Configure Vite's Rollup output chunking to assign only modules belonging to `react`, `react-dom`, and `scheduler` to `react-vendor`. Do not use a catch-all `node_modules` vendor chunk.

This chunk remains a static dependency and therefore counts toward cold-cache initial JavaScript. Its benefit is that changes to application pages can preserve the runtime chunk's content hash and browser cache entry. The implementation must confirm hash stability by building, applying a temporary business-source-only perturbation outside committed files or comparing two known builds, then restoring the source state.

Alternatives considered:

- **Rely entirely on Vite's default chunking:** simplest, but the current single entry invalidates React runtime bytes whenever application code changes.
- **Put every dependency in one vendor chunk:** makes unrelated future dependencies invalidate the stable React cache boundary.
- **Create separate React and ReactDOM chunks:** adds another request without a demonstrated independent update cadence.

### 6. Verify the recursive graph from the Vite manifest

Enable the Vite build manifest and add a dependency-free Node.js bundle checker. Starting from the client entry, it recursively follows static `imports`, sums the raw sizes of all reachable JavaScript files, and sums their individual gzip sizes using `node:zlib`. Dynamic imports are reported separately and excluded from the Dashboard initial graph.

The checker enforces:

- Dashboard initial static graph: at most 232,000 raw bytes and 72,000 gzip bytes.
- All emitted JavaScript: at most 259,541 raw bytes, which is 5% above the verified 247,182-byte baseline.
- Presence of asynchronous entries for the five non-default page modules.
- Absence of those modules from the recursive Dashboard static graph.
- Presence of the targeted `react-vendor` chunk in that static graph.

The current approved-worktree baseline contains additional eager Dashboard presentation code compared with the original estimate. A fresh production build after route splitting measures the full initial static graph at 230,939 raw bytes and 71,766 gzip bytes, including the 192 KB React runtime chunk. The updated limits retain a small regression allowance while still requiring a measurable improvement from the 247,182-byte / 74,538-byte baseline.

The checker reports CSS and fonts separately if included in its output; it never adds them to the JavaScript totals.

## Risks / Trade-offs

- **[Direct deep links still download eager Dashboard code]** → Optimize for the stated Dashboard-first usage; revisit only if navigation analytics show material direct-entry traffic.
- **[Very small asynchronous chunks add request overhead]** → Use Vite's native dynamic-import preload optimization and avoid further chart/helper fragmentation.
- **[Suspense creates two sequential loading surfaces]** → Keep route fallback visually neutral and preserve page feedback for the distinct API-loading phase.
- **[Old deployments leave stale chunk URLs in an open tab]** → Provide an explicit reload action and keep AppShell navigation outside the error boundary.
- **[Manual chunk configuration changes evaluation order]** → Restrict the rule to React runtime packages and run the full frontend test and browser smoke suite.
- **[Bundle budgets become noisy across toolchain upgrades]** → Treat intentional Vite/React upgrades as explicit budget reviews; do not silently loosen thresholds during unrelated work.
- **[Vendor filename remains stable but entry filename changes]** → This is expected; verify cache reuse using the vendor content hash, not the entry hash.
- **[Tests assume synchronous route modules]** → Convert affected assertions to async queries and add explicit pending-import coverage without weakening existing behavior checks.

## Migration Plan

1. Add failing tests for route fallback, route-boundary recovery, and asynchronous route rendering.
2. Introduce top-level lazy page declarations, the route Suspense fallback, and route-scoped error recovery.
3. Add targeted React vendor chunk configuration and enable the Vite manifest.
4. Add the bundle checker and calibrate it against a fresh production build without weakening the defined budgets.
5. Run frontend tests, typecheck, lint, CSS lint, production build, and the bundle checker.
6. Smoke-test Dashboard, each direct deep link, client navigation, history navigation, CommandPalette, throttled route loading, and a failed route chunk.

Rollback consists of restoring static page imports, removing the route Suspense fallback and targeted manual chunk rule, and removing the bundle checker. No persisted data or API migration is involved.

## Open Questions

None. Lazy-loading Dashboard or CommandPalette requires new usage evidence and should be proposed separately rather than folded into this change.
