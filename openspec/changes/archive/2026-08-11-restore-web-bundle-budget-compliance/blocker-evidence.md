# Blocker Evidence: Existing bundle budgets are infeasible with required runtime

**Status:** Blocked (Design Decision 5, Task 2.3 — no credible bounded optimization path)
**Date of measurement:** 2026-08-11
**Command sequence:** `npm --prefix apps/web ci` → `npm --prefix apps/web run build` → `npm --prefix apps/web run check:bundle`

## 1. Reproducible build evidence (Task 2.1)

- Node: `v25.8.2`
- npm: `11.11.1`
- Vite: `7.3.6`
- Lockfile SHA-256: `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34`
- Dependency state: React `^19.0.0`, react-dom `^19.0.0`, react-router-dom `^7.18.2` (from reviewed `package-lock.json`; `npm ci` then fresh build, no `dist/` reuse)

### Initial static graph (Dashboard `/`)

| File | Raw | Gzip |
|---|---|---|
| `assets/index-C6YpcFwz.js` (application entry + Router runtime + shared) | 77,200 | 24,642 |
| `assets/react-vendor-C2StAl4u.js` (react + react-dom + scheduler) | 192,347 | 60,212 |
| **Initial total** | **269,547** | **84,854** |

### Total JavaScript (all emitted chunks)

| File | Raw |
|---|---|
| initial (above) | 269,547 |
| BacktestDetailPage, WalkForwardDetailPage, EtfDetailPage, WalkForwardListPage, SignalListPage, SignalDetailPage, BacktestListPage (7 lazy routes) | 57,702 |
| Pagination, equityCurveChart (shared async chunks) | 1,849 |
| Other initial-shared | — |
| **Total raw** | **329,483** |

### Dynamic route entries (all seven present, none in initial graph / HTML preload)

SignalListPage, SignalDetailPage, BacktestListPage, BacktestDetailPage, EtfDetailPage, WalkForwardListPage, WalkForwardDetailPage — each a separate `isDynamicEntry` chunk; Dashboard HTML does not module-preload them. Chunk ownership is already correct.

### Violations reproduced (checker reports all, no early exit; exits 1)

```
Dashboard initial JavaScript is 269547 bytes, above the 232000-byte budget.
Dashboard initial gzip JavaScript is 84854 bytes, above the 72000-byte budget.
Total JavaScript is 329483 bytes, above the 259541-byte budget.
```

| Metric | Current | Budget | Deficit |
|---|---|---|---|
| Initial raw | 269,547 | 232,000 | +37,547 |
| Initial gzip | 84,854 | 72,000 | +12,854 |
| Total raw | 329,483 | 259,541 | +69,942 |

## 2. Contributor attribution and required-runtime lower bounds (Task 2.2)

Attribution used the real production build plus two isolated builds (same Vite config, same esbuild minifier) to bound required runtime precisely:

| Contributor | Raw | Gzip | Evidence |
|---|---|---|---|
| React 19 runtime (react + react-dom + scheduler, `react-vendor`) | 192,347 | 60,212 | isolated build; identical to real build chunk |
| React Router runtime (`BrowserRouter`, `Routes`, `Route`, `Link`, `useLocation`, `useNavigate`, `useParams`) | ≈ 36,840 | ≈ 13,332 | isolated minimal entry importing exactly the API surface used by `src/App.tsx` |
| **Required runtime lower bound (zero application code)** | **229,187** | **73,544** | — |
| Eager application code in initial graph (entry, AppShell, DashboardPage, CommandPalette, API client, Skeleton, ErrorBoundary) | ≈ 38,956 | ≈ 11,312 | real index chunk minus isolated router runtime |
| Lazy route modules (7 pages + shared helpers) | 59,936 | — | real build, non-initial emitted JS |

Rollup's tree-shaken `renderedLength` and sourcemap segment attribution both agree on the router:application split (~50% of the index chunk each); the isolated router build gives the precise byte figure above.

## 3. Budget-by-budget feasibility (Task 2.3)

### Initial gzip — 72,000 budget: STRUCTURALLY INFEASIBLE
Minimum possible initial gzip = React runtime 60,212 + Router runtime 13,332 = **73,544 bytes**, with **zero** application code. This exceeds the 72,000 budget by **1,544 bytes** of pure required runtime that no application-code optimization can remove. The original budget was calibrated (71,766 gzip, 234-byte headroom) against the pre-Router custom-history app; the Router runtime added by `replace-manual-web-routing-with-react-router` can never fit.

### Total raw — 259,541 budget: STRUCTURALLY INFEASIBLE
Minimum possible total = required runtime 229,187 + lazy feature routes 59,936 = **289,123 bytes**, with **zero** application code. Exceeds 259,541 by **29,582 bytes**. The budget was "5% above the verified 247,182-byte baseline" of the original single-file pre-Router build; required Router runtime + the (already-lazy, feature-mandated) page modules exceed it regardless of any code change.

### Initial raw — 232,000 budget: INFEASIBLE with required eager code
Minimum runtime-only raw is 229,187, leaving only **2,813 bytes** for all eager application code. The contractually eager surface (App entry, AppShell, DashboardPage, CommandPalette, shared API client, Skeleton, ErrorBoundary) measures ≈ 38,956 raw. Fitting it requires cutting ≈ 37,547 bytes — i.e., removing essentially all required eager code, which violates the eager/render contracts.

## 4. Hypotheses evaluated and rejected (no credible closing sequence)

1. **Reduce React vendor runtime** — react-dom 19 ships a pre-bundled production client; Rollup cannot tree-shake it further. 192,347 raw / 60,212 gzip matches the original design's own "192 KB / 60 KB gzip" figure. Only a React replacement (e.g. Preact) would move it, which is a dependency/architecture change requiring a separate approved Change. **Rejected.**
2. **Reduce Router runtime** — already tree-shaken to exactly the API surface used; the routing Change contract requires BrowserRouter as sole route authority in the initial graph. Removing or replacing the router contradicts the active Change. **Rejected.**
3. **Move eager application code out of the initial graph** — AppShell, Dashboard, CommandPalette, API client are contractually eager. Nominal `import()` wrappers are explicitly prohibited (Design Decision 3). **Rejected.**
4. **Remove/reduce lazy route code** — 59,936 raw of feature-mandated page modules; removing them drops product features (Non-Goal). Does not help initial budgets at all. **Rejected.**
5. **Chunk-boundary corrections / duplicate-module removal** — chunk ownership is already correct (all seven routes are separate dynamic entries; no lazy-page code in the initial graph; no duplicated shared modules observed). No such defect exists to exploit. **Rejected.**
6. **Relax or bypass budgets** — explicitly out of scope for this Change ("This Change does not authorize budget relaxation"). **Rejected.**

## 5. Remaining deficits if no change is made

- Initial raw: +37,547 (or +36,143 vs the 2,813-byte realistic headroom)
- Initial gzip: +12,854 (minimum structural deficit +1,544)
- Total raw: +69,942 (minimum structural deficit +29,582)

## 6. User-visible cost of the required runtime

- The required React 19 + React Router runtime costs an additional ≈ 36,840 raw / 13,332 gzip on cold-cache Dashboard load versus the pre-Router custom-history app, plus the Router's incremental contribution to the total graph.
- This cost is not removable while BrowserRouter remains the required route authority and React 19 the required runtime.

## 7. Revised budget bands adopted within this Change

The previous draft candidate values `272,000 / 86,000 / 332,000` were not adopted as
"5%" margins; their actual margins were approximately `0.91% / 1.35% / 0.76%`. The
following smaller, explicit bands are now the in-place contract revision for this Change.

| Band | Current measured baseline | Revised ceiling | Rationale |
|---|---:|---:|---|
| Required React 19 + Router runtime | 229,187 raw / 73,544 gzip | identity-pinned baseline | Any dependency/toolchain identity change requires artifact review |
| Eager application code | ≈38,956 raw / ≈11,312 gzip | 40,000 raw / 12,000 gzip | Small rounded regression allowance |
| Non-initial lazy-route JavaScript | 59,936 raw | 61,000 raw | Small rounded regression allowance |
| Dashboard initial JavaScript | 269,547 raw / 84,854 gzip | 273,000 raw / 86,000 gzip | Current clean-build baseline plus a small explicit margin |
| Total JavaScript | 329,483 raw | 333,000 raw | Current clean-build baseline plus a small explicit margin |

## 8. Conclusion

Bounded, measured optimization **cannot** meet the legacy budgets without violating an existing eager/lazy/routing contract. Task 2.3 therefore remains a valid blocker finding for the legacy contract. The user authorized resolving that incompatibility inside this existing Change through the revised budget bands in section 7; no third Change is created, and the revised contract is implemented and verified below.

## 9. Independent re-audit (2026-08-11)

The current worktree was rebuilt after the original blocker evidence was reviewed. The
focused bundle tests passed (`5 passed`), the fresh Vite build completed, and
`npm --prefix apps/web run check:bundle` reproduced the same three violations:

- initial JavaScript: `269,547` raw / `84,854` gzip;
- total JavaScript: `329,483` raw;
- all seven lazy route entries remained separate, absent from the initial graph, and
  absent from Dashboard module-preload markup.

A sourcemap-only build attributed the current initial graph to ReactDOM client (`176,366`
raw), React Router runtime (`36,523` raw), Dashboard (`19,707` raw), and the remaining
eager application modules. This confirms that the deficit is not caused by a missing
lazy-route boundary or a duplicated page chunk.

As an exploratory lower-runtime check only, a temporary `/private/tmp` build aliased
`react-router-dom@6.30.1`, `react-router@6.30.1`, and `@remix-run/router@1.23.0`; no
repository lockfile or source was changed. The production-style temporary build measured
`254,836` initial raw, `79,874` initial gzip, and `314,772` total raw. React plus the
existing seven lazy feature chunks already measured `252,815` raw; the temporary
sourcemap attribution added approximately `21.3 KB` for the Router v6 runtime. Thus the
runtime plus lazy feature chunks remained approximately `274,111` raw before eager
application code, which is about `14.6 KB` above the total budget. This plausible dependency-only variant
therefore does not provide a compliant path, and adopting it would still require a
separate reviewed dependency/design decision.

## 10. Final revised-contract evidence (2026-08-11)

The applied revision was verified after `npm --prefix apps/web ci` and a fresh
`npm --prefix apps/web run build`:

- Build identity: Node `v25.8.2`, npm `11.11.1`, Vite `7.3.6`, lockfile SHA-256
  `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34`.
- Required runtime: `229,187` raw / `73,544` gzip; identity matches the reviewed
  baseline. The checker independently measures the isolated React vendor at `192,347`
  raw / `60,212` gzip and Router runtime at `36,558` raw / `13,236` gzip, both within
  the reviewed component baselines.
- Eager application: `39,957` raw / `11,228` gzip against `40,000` / `12,000`.
- Non-initial lazy JavaScript: `59,936` raw against `61,000`, including Pagination and
  equity-curve async shared chunks.
- Dashboard initial JavaScript: `269,144` raw / `84,772` gzip against `273,000` /
  `86,000`.
- Total JavaScript: `329,080` raw against `333,000`.
- All seven route entries are separate dynamic entries and remain outside the initial
  graph and Dashboard module-preload markup. Fonts remain reported separately at
  `86,368` raw / `86,375` gzip.
- `npm --prefix apps/web run check:bundle` rebuilt the production bundle itself, then
  returned zero with `violations: []`; it no longer accepts an older `dist/` tree.

The measured application correction removed redundant startup ref synchronization in
`App.tsx` and `CommandPalette.tsx`, consolidated repeated numeric route validation,
removed two no-op keyboard handlers, and removed redundant handler closures. No required
startup module was made dynamic and no budget was rebaselined.

Validation evidence:

- Focused bundle/runtime tests (`11 passed`), full ESLint, CSS lint, typecheck, full Web
  tests (`255 passed, 7 skipped`), fresh build, and bundle check passed. The pre-existing
  untracked `apps/web/attribution.tmp.mjs` attribution helper received only a minimal
  equivalent lint repair so the complete Web gate could run cleanly.
- Fresh browser regression at `1440x1000` and `390x844` rendered Dashboard and Command
  Palette without horizontal overflow or console warnings/errors. Internal Signals →
  Backtests navigation, browser Back/Forward, and direct `/walk-forwards/42` rendering
  passed; fresh screenshots were captured during this validation.
- Automated route-load-failure coverage remains green in the full Web test run.
