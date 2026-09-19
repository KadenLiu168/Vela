# Bundle evidence: build-decision-first-research-workbench

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

## Measured bands

| Band | Before | After | Delta | Revised to |
|---|---:|---:|---:|---:|
| Eager application (raw) | 39,964 | 52,925 | **+12,961** | 53,000 |
| Eager application (gzip) | 11,223 | 14,930 | +3,707 | 15,000 |
| Initial JavaScript (raw) | 269,151 | 282,112 | +12,961 | 283,000 |
| Initial JavaScript (gzip) | 84,767 | 88,474 | +3,707 | 89,000 |
| Lazy route JavaScript (raw) | 69,995 | 66,781 | **−3,214** | 70,000 (unchanged) |
| Total JavaScript (raw) | 339,146 | 348,893 | +9,747 | 349,000 |
| Required runtime (raw) | 229,187 | 229,187 | 0 | 229,187 (unchanged) |

Revised values are the measured value rounded up to the next 1,000, matching
the notation already used in `check-bundle.mjs`. The lazy band was **not**
raised: it improved, because the primary-benchmark and difference formatters
that the Dashboard now shares left the lazy shared-chunk graph.

The initial band is deliberately rounded to 283,000 rather than tracking the
eager band's rounding: before this change the two bands carried very different
headroom (36 bytes above eager, 3,849 above initial), so rounding both by the
same amount left the initial band with too little room for the last
provenance-label addition. The eager band was not raised a second time — the
final eager measurement (52,925) fits the band set by the first revision.

## Lazy route attribution (unchanged ownership)

The checker still locates seven distinct dynamic entries, none of which is in
the Dashboard initial graph:

| Route entry | Raw bytes | Before |
|---|---:|---:|
| `src/pages/SignalListPage.tsx` | 3,555 | 3,555 |
| `src/pages/SignalDetailPage.tsx` | 3,088 | 3,088 |
| `src/pages/BacktestListPage.tsx` | 2,407 | 2,407 |
| `src/pages/BacktestDetailPage.tsx` | 25,007 | 27,381 |
| `src/pages/EtfDetailPage.tsx` | 5,834 | 5,834 |
| `src/pages/WalkForwardListPage.tsx` | 5,076 | 5,076 |
| `src/pages/WalkForwardDetailPage.tsx` | 18,356 | 19,124 |

The Dashboard remains an eager route; no route was added, removed, or merged,
and no code was moved between the eager and lazy graphs to flatter a band.

## Why the eager graph grew

The five decision layers are part of the Dashboard's first screen by
requirement, so they are eager code. The measurement is the real cost of the
reorganisation, not an accounting artifact:

- `researchWorkbench.ts` — the date-fact, benchmark-difference, and OOS
  headline derivations, plus their tests' subject matter.
- `ResearchStatusSection.tsx`, `OosRobustnessSection.tsx` — the two new
  decision-layer regions.
- `panelHeading.tsx` — the shared heading primitive, extracted from
  `DashboardPage.tsx` so the layers and the reference panels render one
  heading implementation (extraction, not addition).
- `DashboardPage.tsx` — the holdings table, the benchmark-difference grid, and
  the signal source label plus its simulated-holdings caveat that replace the
  previous signal/backtest compact lists.
- `signalSourceLabels.ts` — the signal-source vocabulary shared by the Signals
  list and the Dashboard so both name a source the same way.

Net byte growth was minimised first: the reference panels were *moved*, not
duplicated; every new region reuses `dashboard-panel`, `panel-heading`,
`compact-list`, `metric-row`, `holdings-table`, `status-pill`, and
`operation-link`; and no new dependency, route, or API client function was
introduced.

## Verification

`npm --prefix apps/web run check:bundle` exits 0 with `violations: []` after
the revision. The checker's requirement that thresholds are neither bypassed
nor silently rebaselined is satisfied by this file plus the
`web-route-code-splitting` delta in this change.
