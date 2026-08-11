## Context

The active React Router Change correctly places `BrowserRouter` in the application root, so Router runtime is a required member of the initial static graph. A clean production build of the applied routing state measures 269,547 raw / 84,854 gzip initial JavaScript and 329,483 raw total JavaScript. The same build from `HEAD` before the routing diff already measures 232,719 raw / 72,220 gzip initial and 292,721 raw total, above all three established budgets by smaller margins.

The current checker reads Vite's production manifest and correctly includes recursively imported static chunks, but it stops at the first exceeded budget and its expected dynamic-route list predates the Walk-forward pages. The remediation must distinguish required runtime cost, duplicated or misplaced code, avoidable application code, and stale measurement before modifying production boundaries. Existing `web-route-code-splitting` and `web-client-routing` contracts are authoritative: React startup, AppShell, Dashboard, the shared API client, and CommandPalette remain eager; all non-default page modules remain lazy; BrowserRouter remains the sole route authority.

The legacy absolute budgets are not compatible with those contracts. This Change is the
single acceptance decision for that incompatibility: it revises the budget contract in
place instead of creating another active Change. The revised contract is tied to the
reviewed Node/npm/Vite/lockfile identity and separates required runtime from application
allocations so a future dependency change cannot be hidden as a route-splitting win.

## Goals / Non-Goals

**Goals:**

- Produce reproducible, auditable measurements from a clean dependency install and fresh production build.
- Attribute initial and total JavaScript cost sufficiently to choose targeted optimizations rather than guessing.
- Make the current Router-based application pass the revised identity-pinned runtime,
  eager-application, lazy-route, initial-total, and total-JavaScript budgets.
- Keep the legacy-budget blocker and its measured lower bounds auditable while resolving
  the acceptance contract inside this Change.
- Preserve all existing routing, loading, failure-recovery, accessibility, API, and UI behavior.
- Make the checker enumerate every declared lazy route, including Walk-forward history and detail.
- Fail closed with a blocker report if bounded optimization evidence shows the existing contracts and budgets are mutually incompatible.

**Non-Goals:**

- Replacing React, React Router, Vite, or the existing page data-fetching architecture.
- Creating a third Change to own the legacy-budget incompatibility.
- Hiding required startup code behind a nominal dynamic import solely to manipulate manifest accounting.
- Making Dashboard, AppShell, shared navigation, the API client, or CommandPalette lazy contrary to the current specification.
- Changing public routes, backend APIs, database behavior, financial calculations, visual design, or deployment hosting.

## Decisions

### 1. Establish one clean-build evidence contract before optimization

The authoritative workflow is `npm ci` from the reviewed `package-lock.json`, a fresh `npm run build`, then `npm run check:bundle`. The evidence report records Node, npm, Vite, lockfile identity, initial files and raw/gzip totals, all JavaScript files and totals, every dynamic route entry, and the applicable budgets. The checker must evaluate all budgets before exiting so one run exposes every violation, while still returning non-zero if any condition fails.

Using an existing `dist/` tree was rejected because it can report a graph that does not match the reviewed source or dependency identity. Treating Vite's printed per-file list as the contract was rejected because it does not recursively classify the initial graph.

### 2. Diagnose by graph ownership, then apply the smallest measured optimization

Before production edits, derive a module/contributor report for the application entry, React vendor chunk, Router runtime, shared modules, and lazy route modules. Form one optimization hypothesis at a time, add or strengthen a focused structural test, build, and compare raw/gzip/total deltas against the same clean baseline.

The preferred order is:

1. remove unintended eager imports or duplicated modules while preserving ownership contracts;
2. correct chunk boundaries that make lazy-page-only code static or duplicate shared code;
3. simplify evidence-proven application code only when behavior and public component contracts remain unchanged;
4. consider dependency/version or architectural changes only through an explicit design update and fresh review.

This order was chosen over speculative minification flags or broad refactoring because the current deficit spans both initial and total bytes; moving bytes between chunks cannot repair the total budget, and gzip-only tuning cannot repair raw limits.

The revised budget bands are:

| Band | Contract | Current measured baseline | Revised ceiling |
|---|---|---:|---:|
| Required runtime | React 19 + React Router runtime from an isolated build with the reviewed identity | 229,187 raw / 73,544 gzip | identity-pinned; any change requires evidence and artifact review |
| Eager application | Initial graph excluding the isolated required runtime | ≈38,956 raw / ≈11,312 gzip | 40,000 raw / 12,000 gzip |
| Lazy-route aggregate | All non-initial JavaScript, including async shared helpers | 59,936 raw | 61,000 raw |
| Dashboard initial total | All recursively static JavaScript | 269,547 raw / 84,854 gzip | 273,000 raw / 86,000 gzip |
| Total JavaScript | Every emitted JavaScript chunk | 329,483 raw | 333,000 raw |

The revised ceilings are deliberately small, rounded regression margins around the
reviewed clean build, not a claim that the old thresholds remain achievable. The report
must retain the identity and attribution needed to distinguish dependency drift from
application regression.

### 3. Preserve semantic eagerness and count actual cold-cache work

An optimization is valid only if the Dashboard and required shell code render without waiting on a newly introduced application chunk, BrowserRouter remains available before route selection, and the CommandPalette still opens without fetching its own chunk. Every static dependency needed for the initial route remains in initial accounting even if its chunk name changes.

Artificially wrapping required startup modules in `import()` was rejected because it could make the manifest appear smaller while adding a required startup request and violating the eager-render contract.

### 4. Make lazy-route verification derive from the declared route inventory

Bundle validation will cover Signal list/detail, Backtest list/detail, ETF detail, Walk-forward list/detail, and any later route explicitly covered by the capability. Tests will fail if an expected module is absent from the manifest, appears in the initial graph, or is module-preloaded by Dashboard HTML.

A hard-coded five-route list is no longer sufficient because it can pass while the two Walk-forward modules regress into the initial graph. A fully unconstrained “all dynamic entries” assertion was also rejected because non-route dynamic imports may be added later; the expected route inventory remains explicit and reviewable.

### 5. Treat identity drift and revised-band failure as explicit blockers

If the reviewed dependency/tool identity changes, the checker fails closed and requires an
artifact review before accepting a new runtime baseline. If the current identity cannot
meet the revised application allocations or total ceilings without violating an existing
eager/lazy/routing contract, implementation stops and records the lower bounds, attempted
hypotheses, measured deltas, remaining deficits, and user-visible costs in this Change.
No third Change is created implicitly, and no required startup code is made nominally
dynamic to satisfy accounting.

## Risks / Trade-offs

- [The existing total budget may be incompatible with the required React 19 runtime and current feature set] → Calculate required-runtime lower bounds early and stop before broad code churn if the remaining application allowance is demonstrably infeasible.
- [A chunk move can pass initial budgets while total bytes remain unchanged] → Require all three budgets in every comparison and reject accounting-only wins.
- [Dependency upgrades or downgrades can change behavior or lockfile scope] → Treat version changes as a reviewed hypothesis with clean-install tests, exact lockfile diff, full Web gate, and browser regression evidence.
- [Minifier or chunk changes can create runtime-only failures] → Retain route loading/failure tests and perform desktop/narrow browser acceptance after the final production build.
- [Measurement can drift across tool versions] → Record runtime/tool/lock identities and compare only clean builds produced by the same reviewed dependency state.

## Migration Plan

1. Revise this Change's artifacts to record the identity-pinned budget bands and the
   in-place resolution of the legacy-budget blocker.
2. Add failing bundle-analysis tests for clean evidence, complete budget reporting,
   runtime/application/lazy attribution, and the seven-route inventory.
3. Reproduce the current clean Router graph and retain only measured corrections that
   preserve the existing contracts and satisfy the revised bands.
4. Run `npm ci`, the complete Web gate, fresh build, bundle check, and browser acceptance
   on the final stable revision.
5. Complete an independent review of this Change, then re-run final verification for
   `replace-manual-web-routing-with-react-router` before either archival decision.

Rollback is the scoped reversal of bundle-tooling and module-boundary changes. No data or schema rollback exists.

## Open Questions

None before Apply. The artifact revision resolves the legacy-budget incompatibility in
this Change. Apply must first make the revised attribution and budget-band tests
executable; it must not change the reviewed identity or route/eager/lazy contracts as a
shortcut.
