## Context

`GET /api/dashboard` already returns `recent_backtest` from the core dashboard aggregation service. The core service reads the latest persisted `BacktestRun` by `started_at` and id, and API tests already exercise the endpoint against a temporary SQLite database with a real `BacktestRun` row.

The Dashboard page already has a recent backtest panel, but COP-91 requires the empty state to include a clear run-backtest entry point. Full charts and detail-page behavior belong outside this first-screen change.

## Goals / Non-Goals

**Goals:**

- Keep using the existing dashboard aggregate API and `DashboardBacktestSummary` client type.
- Show recent backtest date range, status, and core metrics from the aggregate response.
- Show a clear empty state with a run-backtest entry point when `recent_backtest` is null.
- Validate the behavior with frontend rendering tests and persisted `BacktestRun` API coverage.

**Non-Goals:**

- Do not add a new API route or change the `BacktestRun` schema.
- Do not implement the web action that starts a backtest.
- Do not build charts or full backtest detail content.
- Do not alter signal, market data, or strategy summary behavior.

## Decisions

1. Reuse `GET /api/dashboard` instead of adding a backtest-specific endpoint.
   - Rationale: COP-91 is a Dashboard first-screen summary. The aggregate endpoint already exists for this screen and is backed by persisted `BacktestRun` data.
   - Alternative considered: add `/api/backtests/latest`. Rejected as endpoint expansion beyond the issue scope.

2. Render a disabled `Run backtest` control as the entry point for now.
   - Rationale: existing Dashboard operation controls are disabled placeholders because the web app does not yet implement command execution. This satisfies discoverability without implying an action is wired.
   - Alternative considered: link directly to the CLI command or implement an API action. Rejected because COP-91 is display-focused and full execution belongs in a separate issue.

3. Keep metrics limited to existing summary fields.
   - Rationale: `total_return`, `max_drawdown`, and `sharpe_ratio` are already persisted and exposed. Adding charts or additional metrics would exceed the phase note.

## Risks / Trade-offs

- Disabled entry point may not be executable yet -> label it as the run-backtest entry point while preserving existing local-tool placeholder behavior.
- Existing API tests already cover real `BacktestRun` persistence -> keep focused assertions so validation remains explicit without duplicating the whole backend contract in frontend mocks.
