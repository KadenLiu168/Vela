## Why

COP-90 needs the Dashboard to show the latest usable strategy signal, not just a placeholder or the newest signal row regardless of status. The current frontend shows only a minimal signal summary and the aggregate API does not expose fallback state, so users cannot quickly tell whether the latest successful signal is normal or defensive fallback.

## What Changes

- Update the dashboard aggregate latest signal summary to select the latest `success` signal only.
- Add fallback status to the latest signal summary using persisted signal positions.
- Render signal date, result, fallback status, and target holding count in the Dashboard signal panel.
- Render a clear latest-signal empty state with a generate-signal entry point when no successful signal exists.
- Extend backend/API and frontend tests so validation uses persisted `StrategySignal` data through the real dashboard API contract, not only mocked frontend data.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `dashboard-aggregation`: latest signal summary is defined as the latest successful persisted strategy signal and includes fallback status.
- `http-api-service`: `GET /api/dashboard` returns the expanded latest successful signal summary from persisted SQLite rows.
- `web-frontend-app`: Dashboard latest signal panel renders the expanded latest successful signal summary and explicit empty state/action.

## Impact

- Core dashboard aggregation read model in `packages/core`.
- FastAPI dashboard endpoint response shape.
- Frontend dashboard API types and Dashboard page rendering.
- Focused backend/API/frontend tests and OpenSpec specs.
