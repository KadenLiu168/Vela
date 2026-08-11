## 1. Make bundle evidence complete and mutation-resistant

- [x] 1.1 Add focused failing tests for clean-build identity fields, initial/static graph traversal, total JavaScript measurement, and aggregation of every violated budget without early exit.
- [x] 1.2 Extend the explicit lazy-route inventory and its tests to require separate Signal list/detail, Backtest list/detail, ETF detail, and Walk-forward list/detail entries and to reject initial-graph or Dashboard module-preload ownership.
- [x] 1.3 Update the bundle checker/reporting helpers to satisfy the evidence tests while retaining the legacy `232,000` raw initial, `72,000` gzip initial, and `259,541` raw total thresholds as the pre-revision baseline. The revised contract is defined by task 2.4.

## 2. Establish and resolve the feasibility decision within this Change

- [x] 2.1 From `npm ci` and a fresh production build, produce the current initial/total report with Node, npm, Vite, lockfile, emitted-file, route-entry, and raw/gzip evidence; confirm the reported totals reproduce the existing failure. Evidence recorded in `blocker-evidence.md` section 1: initial 269,547 raw / 84,854 gzip, total 329,483 raw, all three budgets violated.
- [x] 2.2 Produce module/contributor attribution for the application entry, React vendor runtime, Router runtime, shared modules, and lazy routes; calculate the byte deficit and the required-runtime/application lower bounds instead of inferring feasibility from chunk names alone. See `blocker-evidence.md` section 2: required runtime lower bound is 229,187 raw / 73,544 gzip (React 19 + Router only).
- [x] 2.3 Establish whether the legacy budgets can be met without violating eager/lazy/routing contracts. **Outcome under the legacy contract: blocked.** Required runtime alone exceeds the legacy initial-gzip and total-raw ceilings, and the legacy initial-raw ceiling leaves insufficient room for the contractually eager application surface. Full evidence is recorded in `blocker-evidence.md`.

- [x] 2.4 Resolve the legacy-budget incompatibility in this existing Change's artifacts, without creating a third Change: adopt the reviewed-identity runtime baseline (`229,187` raw / `73,544` gzip), eager application allocation (`40,000` raw / `12,000` gzip), lazy-route allocation (`61,000` raw), initial ceilings (`273,000` raw / `86,000` gzip), and total ceiling (`333,000` raw). This is an artifact-only contract revision; no business code or dependency is changed by this task.

## 3. Implement the revised evidence contract without accounting tricks

- [x] 3.1 Add focused failing tests for reviewed build identity, required-runtime attribution, eager-application allocation, lazy-route allocation, revised initial/total ceilings, and complete violation reporting.
- [x] 3.2 Extend the bundle reporting/checking helpers to compute the revised bands from a fresh manifest and reviewed identity while retaining separate seven-route ownership checks and font/JavaScript separation.
- [x] 3.3 Apply the smallest measured module/import/chunk correction only if the current build exceeds a revised application allocation; retain only changes that reduce the targeted metric while all focused behavior and graph tests pass.
- [x] 3.4 Repeat the evidence-driven optimization loop only as needed until the fresh build satisfies the revised contract; do not make required startup code nominally dynamic, silently rebaseline, or broaden unrelated frontend refactoring.

## 4. Validate behavior and dependent Change readiness

- [x] 4.1 Run `npm --prefix apps/web ci`, Web lint, CSS lint, typecheck, full tests, and a fresh production build, then run `npm --prefix apps/web run check:bundle` and record every final measurement against the revised bands.
- [x] 4.2 Perform browser regression at 1440x1000 and 390x844 for Dashboard eager render, command-palette immediate availability, direct and internal Router navigation, Back/Forward, lazy-route loading, and page-level overflow/console health; retain focused automated coverage for rejected-chunk failure and navigation recovery.
- [x] 4.3 Run `openspec validate restore-web-bundle-budget-compliance --strict`, `openspec validate replace-manual-web-routing-with-react-router --strict`, broader OpenSpec health checks, and `git diff --check`; review the final diff for unrelated work, unchanged API/database scope, and no third Change.
- [x] 4.4 Complete a fresh independent post-implementation review of this Change; only after it passes, re-run the final review and complete gate for `replace-manual-web-routing-with-react-router` before recommending either Change for archival.
