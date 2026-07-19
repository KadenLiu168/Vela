## 1. Route Loading Tests

- [x] 1.1 Add failing App tests proving a pending non-default route import keeps AppShell navigation visible and exposes an accessible `Loading page` Skeleton fallback.
- [x] 1.2 Add failing tests proving direct visits and client navigation still render all five non-default routes with their existing API, loading, success, empty, and error behavior after asynchronous module resolution.
- [x] 1.3 Add failing tests proving a rejected route import renders a reload action and navigation to another path resets the route-scoped error state.

## 2. Route Boundary Implementation

- [x] 2.1 Replace the five non-default page static imports in `apps/web/src/App.tsx` with top-level `React.lazy` loaders while keeping DashboardPage and CommandPalette eager.
- [x] 2.2 Add the route-level Suspense boundary inside AppShell and compose its accessible layout-stable fallback from the existing Skeleton primitive.
- [x] 2.3 Extend the existing ErrorBoundary usage with a route-load failure fallback and reload action, and key the route boundary by the full current path so navigation recovers from failures.
- [x] 2.4 Update affected route tests to await lazy rendering without weakening their existing heading, navigation, data, and history assertions.

## 3. Production Chunking and Bundle Checks

- [x] 3.1 Add targeted Vite chunk configuration that emits only React, ReactDOM, and Scheduler modules in `react-vendor`, and enable the production manifest.
- [x] 3.2 Add fixture-driven tests for a dependency-free manifest analyzer that recursively identifies the initial static graph, separates dynamic entries, and calculates raw and gzip JavaScript sizes.
- [x] 3.3 Implement the production bundle checker and package script, enforcing the 232,000-byte raw and 72,000-byte gzip Dashboard initial budgets plus the 259,541-byte total raw JavaScript budget.
- [x] 3.4 Build twice around a reversible application-source-only perturbation and verify the content-hashed `react-vendor` filename remains stable while the application entry filename changes.
- [x] 3.5 Verify the manifest reports all five non-default page modules as dynamic entries, excludes them from the Dashboard static graph and HTML modulepreloads, and includes `react-vendor` in cold-cache totals.

## 4. Verification

- [x] 4.1 Run the frontend test, typecheck, ESLint, Stylelint, CSS root, production build, and bundle-budget commands and resolve failures without loosening unrelated checks.
- [x] 4.2 Browser-smoke-test `/`, every direct non-default route, client navigation, back/forward history, and CommandPalette with a cold cache.
- [ ] 4.3 Under network and CPU throttling, verify AppShell persistence and accessible route loading, then simulate a failed route chunk and verify reload and navigation recovery.
- [x] 4.4 Record before/after initial static graph, dynamic route chunks, total JavaScript, CSS, and font sizes as separate measurements, without attributing font-subsetting results to this change.
