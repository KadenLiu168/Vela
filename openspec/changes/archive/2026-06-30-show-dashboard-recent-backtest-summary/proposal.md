## Why

COP-91 needs the Dashboard to make the most recent persisted backtest run reviewable from the first screen. The aggregate API already exposes recent `BacktestRun` data, but the frontend contract should explicitly cover populated and empty recent-backtest states, including a run-backtest entry point when no run exists.

## What Changes

- Render the Dashboard recent backtest panel with the latest persisted run date range, status, and core metric summary.
- Add an explicit empty recent-backtest state that includes a run-backtest entry point.
- Extend validation so recent backtest behavior is covered by the real dashboard API backed by persisted `BacktestRun` rows, not only mocked frontend responses.
- Do not implement charts, a full backtest detail page, or a runnable web backtest action in this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add explicit Dashboard recent backtest populated, empty, and real API-backed validation requirements.

## Impact

- Affected frontend code: `apps/web/src/pages/DashboardPage.tsx` and focused dashboard tests.
- Affected API/core validation: existing dashboard API/core tests may be tightened for persisted `BacktestRun` coverage if needed.
- Affected OpenSpec specs: `openspec/specs/web-frontend-app/spec.md`.
- No database schema, API route, or new dependency changes.
