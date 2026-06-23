## Why

Backtesting needs a deterministic daily net value curve before later work can persist results or calculate performance metrics. COP-58 adds the core calculation step that turns daily target holdings and market prices into a strategy equity curve.

## What Changes

- Add a core backend capability to calculate strategy net value points for a requested trading-date range.
- Use existing portfolio holding snapshots and market price strategy prices to compute daily weighted portfolio returns.
- Define the initial net value as `1.000000` and roll each following day's net value forward from the prior calculated point.
- Keep the change in core business logic and tests; no CLI, API, database schema, or persistence workflow changes.

## Capabilities

### New Capabilities
- `strategy-equity-curve`: Calculate daily strategy net value curve points from portfolio holdings and market price returns.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/core/src/vela_core/`, especially a new equity curve calculation helper and public exports.
- Affected tests: `packages/core/tests/` unit tests for initial net value, weighted daily returns, carried holdings, and missing price behavior.
- Affected specs: new OpenSpec capability under `openspec/changes/calculate-strategy-equity-curve/specs/strategy-equity-curve/spec.md`.
- Dependencies and storage: no new runtime dependencies and no database migration.
