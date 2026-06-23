## Why

Users need a local CLI command that turns the configured ETF rotation strategy and locally stored market prices into the latest persisted strategy signal. This completes the Phase 1 backend path from fetched market data to a stored signal that can be inspected by later workflows.

## What Changes

- Add a `generate-signal` CLI command that accepts a database URL, strategy config path, and optional signal date.
- Generate a strategy signal from local `MarketPrice` rows by scoring active ETFs, applying Top N selection with defensive fallback, and persisting the result.
- Print a concise signal summary including status, result, signal date, config version, signal id, and selected positions.
- Report generation failures clearly and exit non-zero without adding unrelated COP-54 behavior.

## Capabilities

### New Capabilities

- `strategy-signal-generation`: Core strategy signal generation from stored market prices and strategy configuration.

### Modified Capabilities

- `cli-database-initialization`: Expose and report the `generate-signal` local CLI workflow.
- `strategy-signal-model`: Persist generated signals through the existing signal persistence contract.

## Impact

- Affected code: `packages/core/src/vela_core`, `packages/core/tests`, `apps/cli/src/vela_cli/main.py`, and `apps/cli/tests`.
- No database schema changes.
- No new external dependencies.
