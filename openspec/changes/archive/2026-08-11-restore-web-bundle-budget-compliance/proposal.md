## Why

The production Web bundle exceeded the legacy `web-route-code-splitting` budgets before
the React Router migration, and the required React 19 + BrowserRouter runtime makes the
legacy thresholds structurally incompatible with the routing contract. The current clean
Router build measures 269,547 raw / 84,854 gzip initial JavaScript and 329,483 raw total
JavaScript. The blocker was discovered while reviewing
`replace-manual-web-routing-with-react-router`; creating another active Change would
split ownership of the same acceptance decision.

This Change therefore resolves the incompatibility in place. It retains the existing
route and eager/lazy behavior contracts while replacing the obsolete absolute budget
contract with an identity-pinned runtime baseline and measured application allocations.

## What Changes

- Make a clean production build and Vite-manifest analysis the authoritative evidence for
  initial raw/gzip size, total raw size, static imports, and every lazy route entry.
- Report the required React/Router runtime baseline separately from eager application code
  and the aggregate non-initial lazy-route JavaScript.
- Adopt the evidence-backed budgets for the current reviewed identity: required runtime
  baseline 229,187 raw / 73,544 gzip; eager application allocation 40,000 raw / 12,000
  gzip; lazy-route aggregate 61,000 raw; initial total 273,000 raw / 86,000 gzip; and
  total JavaScript 333,000 raw.
- Preserve Dashboard/AppShell/CommandPalette eagerness, declarative browser routing, lazy
  non-default pages, route loading/failure recovery, public paths, and existing API/UI
  behavior while enforcing the revised contract.
- Extend bundle verification to cover every declared lazy route module, including both
  Walk-forward routes, and add focused regression coverage for graph classification,
  identity-pinned attribution, budget bands, and complete violation reporting.
- If the current reviewed identity or measured application allocations exceed the revised
  contract, stop with an auditable blocker in this same Change; do not silently create a
  third Change, hide required startup code, or weaken route ownership.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-route-code-splitting`: Require clean-build evidence for the current Router-based graph, identity-pinned runtime/application/lazy attribution, revised budget-band enforcement, comprehensive lazy-route accounting, and preservation of eager/lazy runtime ownership during bundle remediation.

## Impact

- Affected frontend build and bundle tooling: `apps/web/vite.config.ts`, `apps/web/scripts/check-bundle.mjs`, `apps/web/scripts/bundle-manifest.mjs`, and focused bundle-analysis tests.
- Potentially affected frontend module boundaries or imports are limited to evidence-backed changes needed to remain within the revised allocations; public paths, Router behavior, page APIs, visual behavior, and accessibility contracts remain unchanged.
- The active `replace-manual-web-routing-with-react-router` Change remains dependent on this Change's final bundle and browser gate before final verification and archival; both acceptance decisions remain represented by these two existing Changes.
- No backend API, Python package, database schema, migration, persistent `vela.db`, deployment host, or financial-calculation behavior changes.
