## 1. Reproduce and attribute the failing graph

- [x] 1.1 Confirm the Git root and preserve the existing pnpm deletions, `remove-stale-pnpm-state`, database sidecars, and all unrelated work; record the unchanged `apps/web/package-lock.json` hash plus Node/npm/Vite identity. Re-run `npm --prefix apps/web ci` only if `node_modules` is missing/untrusted or clean-install reproduction is required.
- [x] 1.2 Run `npm --prefix apps/web run check:bundle` to perform a fresh production build, retain the expected failing exit, and record all budget bands plus every emitted initial, route-entry, and non-initial shared JavaScript file in `optimization-evidence.md`; reconcile the route/shared rows exactly to 77,211 lazy raw bytes and the complete graph to 346,363 total raw bytes.
- [x] 1.3 Using only the installed Vite/Rollup toolchain, attribute rendered module contributors for each of the seven route chunks, prioritizing the 31,827-byte Backtest detail and 22,201-byte Walk-forward detail entries; document duplicate-code, unused-code, and import-boundary hypotheses without changing dependencies or production behavior.

## 2. Make route-level evidence regression-testable

- [x] 2.1 Add focused failing cases to `apps/web/scripts/bundle-manifest.test.mjs` for per-route raw-byte reporting, separately listed non-initial shared chunks, exact lazy-aggregate reconciliation, and shared chunks counted once.
- [x] 2.2 Make the minimum changes to `apps/web/scripts/bundle-manifest.mjs` and, only if needed for output, `apps/web/scripts/check-bundle.mjs` so the focused tests pass and the fresh failing report exposes all seven route entries and shared chunks without changing any budget value or identity check.
- [x] 2.3 Run `npm --prefix apps/web run test -- scripts/bundle-manifest.test.mjs` and a fresh `npm --prefix apps/web run check:bundle`; record the unchanged pre-optimization totals and confirm reporting alone neither moves nor removes bytes.

## 3. Remove measured emitted JavaScript

- [x] 3.1 Trace every caller and behavior contract of the highest-value duplicate/unnecessary contributor identified in task 1.3; add or retain the smallest focused page/helper test that would fail if its user-visible, financial-formatting, empty/error, accessibility, or route-loading behavior changed.
- [x] 3.2 Apply one surgical removal, reuse of an existing helper/component, or correction of a duplicate import boundary; run its focused tests and a fresh build, then retain it only if it lowers both the targeted lazy measurement and total JavaScript without increasing initial bands or changing route ownership.
- [x] 3.3 Repeat task 3.1–3.2 only for evidence-ranked contributors until lazy JavaScript is below the 70,000-byte ceiling, preferably below 69,000 for margin, and total JavaScript is at or below 340,000; record each retained/rejected hypothesis and exact delta in `optimization-evidence.md`.
- [x] 3.4 Confirm nested dynamic imports, eager-code moves, route-entry merging, minifier changes, dependency changes, and budget increases were not used as accounting shortcuts; verify all seven React Router page modules remain distinct lazy entries and `apps/web/package-lock.json` is unchanged.

## 4. Complete Web and specification verification

- [x] 4.1 Run focused tests for every changed production page/helper, then run the complete Web gate from the repository root: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 4.2 Run `npm --prefix apps/web run check:bundle` after the full gate and record the final route-by-route table, lazy/total headroom, passing build identity, runtime/eager/initial bands, route ownership, and lockfile hash in `optimization-evidence.md`.
- [x] 4.3 Perform browser regression at 1440×1000 and 390×844 for Dashboard eager render and direct/internal navigation to Backtest and Walk-forward detail pages, checking loading/error recovery, content/interaction parity, console errors, failed network requests, and horizontal overflow.
- [x] 4.4 Run `openspec validate optimize-web-bundle-size --strict`, `openspec validate --all --strict`, `openspec doctor`, and `git diff --check`; review the final diff to confirm only evidence-proven bundle/frontend files and this Change were touched, while `remove-stale-pnpm-state`, ECO-56, dependencies, `package-lock.json`, APIs, backend/database files, and persistent `vela.db` remain unchanged.
