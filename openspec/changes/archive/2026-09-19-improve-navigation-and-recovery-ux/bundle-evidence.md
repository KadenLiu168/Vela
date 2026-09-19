# Bundle evidence: improve-navigation-and-recovery-ux

`web-route-code-splitting` requires bundle acceptance evidence to come from a
fresh production build of the changed source, to identify the build identity,
to attribute every lazy route entry separately, and to revise a pinned band
only as an explicit, recorded action. This file records that evidence.

## Build identity

| Field | Value |
|---|---|
| Node | v25.8.2 |
| npm | 11.11.1 |
| Vite | 7.3.6 |
| lockfile sha256 | `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34` |

Unchanged from the reviewed identity: no dependency, toolchain, or lockfile
change is part of this change.

## Command

```bash
npm --prefix apps/web run check:bundle
```

The checker rebuilds `dist/`, derives the static/dynamic chunk graph from the
fresh Vite manifest, and evaluates every band in one run.

## Baseline

The "Before" column is **quoted** from the immediately preceding,
still-unarchived `build-decision-first-research-workbench` and its
`bundle-evidence.md` — it is the recorded measurement of this same worktree
without this change, not a re-measurement. The two changes are stacked on one
working tree; see "Archive order" below. (That record states `initial gzip` as
88,474 in its table and 88,560 in the `check-bundle.mjs` comment it wrote; the
86-byte discrepancy does not affect this revision, since both fit the existing
89,000 allocation that this change leaves in place.)

## Measured bands

| Band | Before | After | Delta | Revised to |
|---|---:|---:|---:|---:|
| Eager application (raw) | 52,925 | 54,402 | **+1,477** | 55,000 |
| Eager application (gzip) | 14,930 | 15,470 | +540 | 16,000 |
| Initial JavaScript (raw) | 282,112 | 283,589 | +1,477 | 284,000 |
| Initial JavaScript (gzip) | 88,474 | 89,014 | +540 | 90,000 |
| Lazy route JavaScript (raw) | 66,781 | 69,446 | +2,665 | 70,000 (unchanged) |
| Total JavaScript (raw) | 348,893 | 353,035 | +4,142 | 354,000 |
| Required runtime (raw) | 229,187 | 229,187 | 0 | 229,187 (unchanged) |

`initialGzip` was raised in a second pass: 88,972 fitted the previous 89,000
allocation, but the StrictMode guard added to the route-transition effect (see
"Route-transition StrictMode defect" below) took it to 89,002 — two bytes past
the allocation — so the band was revised to 90,000. `lazyRouteRaw` was **not**
raised: 69,446 still fits its 70,000 band, leaving **554 raw bytes** of
headroom. The three history pages were consolidated onto one query-string
module (`listQuery.ts`) after the first measurement, which is what moved the
band from 69,964 back to 69,446: the same rule had been written out three
times, and the shared module is counted once.

## Route-transition StrictMode defect

Browser verification of this change found a defect that the jsdom suite could
not: the route-transition effect was not idempotent. `main.tsx` mounts the app
in `StrictMode`, which invokes a mount's effects twice; the first invocation
consumed the "has navigated" latch, so the second was read as a navigation and
the initial document load took focus on the page `<h1>` and reset the reading
position. The guard ref that fixes it costs 52 raw / 30 gzip bytes in the eager
graph, and it is what pushed `initialGzip` past its previous allocation.

The navigation suite now mounts the app under `StrictMode` so that a
non-idempotent transition effect fails there too. Verified by disabling the
guard: without it, `does not move focus on the initial document load` fails.

## What the growth is

Eager growth is the three pieces that must run on every route and therefore
live in the eagerly loaded graph:

- `RouteTransition` (reading-position reset, heading focus, document title
  hand-off) in `App.tsx`;
- the `ReadFailure` primitive and its pure `describeReadFailure` cause
  mapping, which the eager `DashboardPage` renders;
- the `AppShell` skip link and the `main` focus target.

Lazy growth is the three history pages carrying their pagination offset
through the URL, recording the list location their rows were clicked from, and
rendering `ReadFailure`; plus the four detail pages carrying their back link,
title, and retry; plus the row-range statement the paginated lists render.

## Route-splitting contract

`dynamicRouteEntries` still lists all seven lazy page modules as independent
dynamic entries:

```
assets/SignalListPage-*.js
assets/SignalDetailPage-*.js
assets/BacktestListPage-*.js
assets/BacktestDetailPage-*.js
assets/EtfDetailPage-*.js
assets/WalkForwardListPage-*.js
assets/WalkForwardDetailPage-*.js
```

Dashboard remains eager. No new shared chunk was introduced; the new
`listOffset` helper lands as its own small shared chunk (118 raw / 115 gzip)
between the list pages.

## Archive order

`build-decision-first-research-workbench` and this change both revise the same
budget bands in `web-route-code-splitting`. Both write their revision as a
change delta; the main spec has not yet absorbed the earlier one. **The earlier
change must be archived first.** If this change were archived first, its delta
would rewrite the band numbers from the main spec's pre-`build-decision-first`
values (40,000 / 273,000 / 340,000) and silently discard the earlier revision.
