## Context

See `proposal.md` for motivation. The fresh npm production graph currently reports 77,211 raw bytes of non-initial JavaScript and 346,363 raw bytes across all JavaScript. Its non-initial manifest entries are:

| Emitted owner | Raw bytes |
|---|---:|
| Backtest detail route | 31,827 |
| Walk-forward detail route | 22,201 |
| ETF detail route | 5,834 |
| Walk-forward list route | 5,076 |
| Signal list route | 3,555 |
| Signal detail route | 3,088 |
| Backtest list route | 2,407 |
| Shared `equityCurveChart` chunk | 2,812 |
| Shared `Pagination` chunk | 411 |

The 7,211-byte lazy deficit and 6,363-byte total deficit therefore share one lower bound: at least 7,211 emitted non-initial bytes must be removed, not merely moved. `BacktestDetailPage` and `WalkForwardDetailPage` are the first attribution targets because together they own 54,028 bytes, but source size alone is not proof that either contains removable code.

The checker counts every emitted non-initial JavaScript file. Splitting a detail subsection into another dynamic chunk or moving it into the initial graph cannot reduce total JavaScript, and nested lazy loading alone cannot reduce the existing lazy aggregate. The seven page modules must remain distinct React Router lazy entries; required runtime, AppShell, Dashboard, the API client, and CommandPalette remain eager.

The current `check-bundle.mjs` ceilings of 70,000 lazy and 340,000 total came from the 2026-08-12 Backtest redesign build (68,062 lazy and 337,206 total). They provided only 1,938 and 2,794 bytes of measured margin and retained identity/runtime checks. The living spec was not synchronized and still says 61,000/333,000. This Change corrects that documentary drift; it does not raise the executable gate.

## Goals / Non-Goals

**Goals:**

- Explain each route entry and shared async chunk before production edits.
- Remove at least 7,211 raw lazy bytes and retain practical margin below 70,000; every retained optimization must also lower total JavaScript.
- Keep measurements reproducible under the current Node/npm/Vite/lockfile identity.
- Preserve functional, routing, loading, accessibility, and visual contracts with focused tests and the complete Web gate.

**Non-Goals:**

- Changing dependencies, `package-lock.json`, minifier settings, public routes, APIs, backend/database behavior, or financial semantics.
- Making currently eager features lazy, merging the seven route entries, or redefining lazy bytes to exclude emitted async code.
- Broadly redesigning Backtest or Walk-forward UI, or optimizing test-source size.
- Modifying `remove-stale-pnpm-state` or doing ECO-56 work.

## Decisions

### 1. Add route-level evidence before choosing code changes

Extend the existing manifest analysis and its tests to report each dynamic route entry's emitted raw bytes plus separately emitted non-initial shared chunks. For source-level diagnosis, use the already installed Vite/Rollup build metadata in a temporary or narrowly scoped diagnostic and record module contributors in `optimization-evidence.md`; do not add a bundle-analyzer dependency or change `package-lock.json`.

The report must reconcile exactly to 77,211 before optimization and to the final lazy aggregate afterward. Chunk filenames alone were rejected because they identify owners but not duplicated or unexpectedly retained source. Source line counts were rejected because minification and tree shaking determine the emitted result.

### 2. Optimize one measured hypothesis at a time

Start with the two largest route chunks and trace their imports and rendered module contributors. For each candidate, add or retain the smallest behavior/structure regression test, make one surgical change, build with the same identity, and compare route, lazy, initial, total, raw, and gzip deltas. Revert candidates that only move bytes, increase total, or lack a clear ownership explanation.

Use this order:

1. remove unreachable, redundant, or duplicated production logic and literals;
2. reuse an existing helper/component when two emitted implementations have the same semantic contract and the build proves a net reduction;
3. correct an accidental import boundary that emits the same implementation more than once;
4. consider nested lazy loading only for a separately demonstrated route-interaction benefit, never as evidence that the aggregate budgets improved.

New generalized component layers, dependencies, minifier flags, and speculative rewrites are rejected. A shared abstraction that does not reduce the fresh build is also rejected even if source code looks drier.

### 3. Keep the current executable ceilings and require margin

Acceptance requires lazy JavaScript at or below 70,000 raw bytes and total JavaScript at or below 340,000 raw bytes, with all other identity and graph checks passing. The working target is below 69,000 lazy bytes so ordinary content-hash/minifier noise does not leave the result exactly on the boundary; 70,000 remains the normative ceiling.

The living-spec update from 61,000/333,000 to 70,000/340,000 is justified by the already accepted Backtest redesign evidence and current executable gate. It is not a new relaxation: no checker value changes, identity remains pinned, all other bands remain fixed, and this Change must reduce the current build back under those ceilings.

If bounded, behavior-preserving removal cannot reach the ceilings, Apply stops with contributor evidence, attempted deltas, remaining deficit, and user-visible trade-offs. Raising either executable ceiling would require an explicit revision to this Change and review of fresh evidence; it is not an implementation fallback.

### 4. Preserve ownership and behavior with existing tests plus focused bundle tests

Keep the current module-level `React.lazy` imports and distinct manifest entries. Extend `bundle-manifest.test.mjs` for route/shared-chunk byte reconciliation and retain existing route-loading/failure tests. Run focused tests for every changed page/helper, then the repository-defined complete Web gate and `check:bundle`, which performs its own fresh production build.

No clean install is needed during ordinary iteration because dependency files remain unchanged and the current `node_modules` state was already validated. Final acceptance runs `npm --prefix apps/web ci` only if dependency state is missing/untrusted or clean-install reproduction is explicitly required; otherwise the unchanged lockfile hash and identity checks are sufficient.

## Risks / Trade-offs

- [A visually duplicate block has subtly different financial or empty-state semantics] → Reuse code only after comparing both caller contracts and retain focused behavior tests for each route.
- [Extracting a shared helper adds wrappers or prevents tree shaking] → Keep only fresh-build changes that reduce both the targeted route/lazy measurement and total JavaScript.
- [Moving code between chunks produces an accounting-only pass] → Require total reduction of at least the remaining total deficit and exact reconciliation of all emitted non-initial files.
- [The build changes under a different toolchain] → Keep Node/npm/Vite/lockfile identity checks fail-closed and do not update dependencies in this Change.
- [A minimal optimization lands too close to the threshold] → Target below 69,000 lazy bytes and record final headroom; the hard contract remains 70,000.

## Migration Plan

1. Capture the fresh failing baseline and contributor attribution under the reviewed identity.
2. Add route/shared-chunk reporting tests and the smallest reporting change.
3. Apply and measure one optimization hypothesis at a time; retain only behavior-preserving net reductions.
4. Run focused tests, the complete Web gate, a final fresh bundle check, strict OpenSpec validation, and diff checks.

Rollback is a scoped revert of this Change's bundle-reporting and frontend optimization files. There is no dependency, database, schema, or data migration.
