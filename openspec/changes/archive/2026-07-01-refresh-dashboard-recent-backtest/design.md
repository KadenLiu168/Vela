## Context

The Dashboard currently loads persisted aggregate state from `GET /api/dashboard` on page load. COP-108 added an Operations panel summary that renders the immediate `POST /api/backtests/run` response, but the Recent backtest panel still depends on the Dashboard aggregate state captured before the run.

The backend already persists backtest runs and exposes the latest persisted run through `DashboardResponse.recent_backtest`.

## Goals / Non-Goals

**Goals:**

- Refresh Dashboard aggregate state after a successful Dashboard backtest submission.
- Keep the Recent backtest panel sourced from `DashboardResponse.recent_backtest`.
- Preserve the existing immediate Operations panel run summary and detail link.
- Cover browser-refresh behavior through Dashboard initial-load tests.

**Non-Goals:**

- Do not add a new backtest status endpoint.
- Do not change `POST /api/backtests/run` or `GET /api/dashboard` response schemas.
- Do not implement a full Backtest Detail page.
- Do not add polling or background refresh.

## Decisions

- Reuse `loadDashboard(setDashboardState)` after `runBacktest()` succeeds.
  - Rationale: `GET /api/dashboard` is already the persisted first-screen read model and includes `recent_backtest`.
  - Alternative considered: synthesize a `DashboardBacktestSummary` from `BacktestRunResponse` locally. That would not prove the panel is reading the same persisted backend result and would need extra fields not returned by the run endpoint, such as `strategy_name`, `config_version`, and `started_at`.
- Keep `backtestRunResult` for the Operations panel.
  - Rationale: COP-108 requires immediate run response details including trading day count and signal count, which are not part of the Dashboard recent backtest summary.
- Do not refresh Dashboard after failed backtest submissions.
  - Rationale: failures do not persist a successful recent backtest result and existing scoped error behavior should remain stable.

## Risks / Trade-offs

- Dashboard refresh fails after a successful run -> The Operations panel still shows the successful run response, while the Dashboard-level error state can surface API unavailability.
- Extra Dashboard request after successful run -> Acceptable for Phase 1 because the workflow is user-triggered and avoids local data synthesis.
