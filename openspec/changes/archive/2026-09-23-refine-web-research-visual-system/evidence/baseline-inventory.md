# Baseline inventory — before any visual change (task 1.1)

Recorded at git HEAD `3eafd31e` (feat(web): redesign visual system), working tree
clean except this Change directory, `vela.db-shm`/`vela.db-wal` (untracked, untouched).

## Routes (8 business routes + 404)

| Route | Component | Notes |
| --- | --- | --- |
| `/` | `DashboardPage` (eager) | five research layers + reference/operations grid |
| `/signals` | `SignalListPage` (lazy) | source column |
| `/signals/:signalId` | `SignalDetailPage` (lazy) | numeric-id guard |
| `/backtests` | `BacktestListPage` (lazy) | |
| `/backtests/:backtestId` | `BacktestDetailPage` (lazy) | Overview/Signals tabs |
| `/walk-forwards` | `WalkForwardListPage` (lazy) | run trigger |
| `/walk-forwards/:runId` | `WalkForwardDetailPage` (lazy) | |
| `/etfs/:etfId` | `EtfDetailPage` (lazy) | |
| `*` | `NotFoundPage` | |

Shared: `AppShell` (brand + nav + api meta), `CommandPalette` (Cmd+K / `/`),
`ErrorBoundary`, `Skeleton`, lazy `Suspense` fallback, `RouteTransition`
(focus/scroll on navigation).

## Dashboard research order (verified against research-workbench-ui)

`research-decision-path` children in DOM order:

1. `ResearchStatusSection` — current state
2. signal panel (`workflow-panel-signal`) — latest signal
3. backtest panel (`workflow-panel-backtest`) — strategy performance
4. `OosRobustnessSection` — OOS robustness
5. `EvidenceIndexSection` — deep evidence drill-down

Then `dashboard-grid` (reference/operations): market panel (`#dashboard-etf-coverage`),
strategy panel, operations panel, fetch-log panel. ✓ matches spec
"Research hierarchy preserves evidence and workflow order" baseline.

## Backtest Detail order (verified against backtest-results-ui)

Overview tab: run summary (`p.run-summary`) → `DecisionSummarySection` →
Equity curve (`holdings-section` + `EquityCurveChart`) →
`BenchmarkComparisonSection` → `DeepAnalysisSection` → `ExperimentConfigSection`.
Signals tab: table + pagination. ✓ six-section order confirmed.

## Token consumers (styles.css, count of `var(--x)` occurrences ≥4)

font-sans 59, spacing-16 53, spacing-12 50, spacing-8 46, text-secondary 43,
border-subtle 40, text-primary 37, leading-body-card 35, card-body-size 35,
spacing-20 33, text-tertiary 31, radius-md 26, surface-panel 25,
font-weight-medium 25, font-mono 25, card-meta-size 25, leading-meta 24,
tracking-meta 22, surface-raised 21, font-weight-label 20, font-weight-regular 15,
tracking-numeral 13, ease-out 13, border-strong 13, spacing-24 11,
interactive-primary 10, spacing-4 9, section-gap 9, duration-base 8,
tracking-title 7, spacing-32 7, text-section-title 6, surface-hover 6,
status-danger 6, radius-sm 6, leading-section-title 6, font-weight-title 6,
card-padding-y 6, card-padding-x 6, status-info 5, radius-xl 5,
focus-ring-color 5, duration-fast 5, text-label 4, surface-canvas 4,
status-success 4, spacing-40 4, text-body 3, radius-pills 3, market-up 3,
market-down 3, leading-label 3, leading-emphasis 3, leading-dense 3,
leading-body 3, chart-primary-line 3, chart-axis 3, card-emphasis-size 3,
text-chart-axis 2, text-card-title 2, leading-page-title (page-title rules).

Not yet consumed anywhere: `--space-*` ladder, `--shadow-*` most entries,
`--duration-slow`, `--status-warning` (palette only), most chart series tokens.

## Current geometry (pre-change)

- `--section-gap: 96px` (top-level research sections), `--card-padding-y: 20px`
  (x: 24px), `--card-padding: 24px`, `--card-shadow: var(--shadow-subtle-3)`,
  `--card-bg: var(--surface-raised)`.
- Breakpoints (styles.css): 1024 / 900 / 720 px, shell padding
  40/32 → 36/24 → 20, panels expand to 32px at ≤1024 (detail pages) —
  the density inversion called out in design.md.
- Motion: durations only via tokens; reduced-motion block zeroes nav/buttons/
  inputs/links + skeleton pulse.

## Gaps this Change must close (from deltas)

- design-system: new layout/control tokens (gutters, group-gap,
  heading-content-gap, control heights, compact page title, card padding
  compact), panel surface role split, motion clarifications.
- card-type-scale: important date values/counts ≥ 12/16 label role;
  status/risk/unavailable ≥ 13/20 dense role; compact-list keeps 11/20 + 13/20.
- detail-page-typography-consistency: shared page-title roles across pages
  (36/40 desktop, 28/36 ≤720px); removes stale `text-heading-sm` references.
- web-frontend-app: AppShell brand 22/28 620 -0.035em (already matches);
  research order retention; narrow-screen completeness; AA target;
  reproducible acceptance harness.
