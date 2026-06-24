## Why

COP-66 needs a human-readable report for persisted backtest results so local validation can inspect the core metrics and equity curve summary after `run-backtest` completes. The existing backtest persistence query loads by run id, but there is no formatter or CLI export command.

## What Changes

- Add a core backtest report exporter that loads a persisted run by id.
- Format run metadata, core metrics, and a concise equity curve summary.
- Include curve point count, first and last curve rows, and min/max net value rows.
- Add an `export-backtest-report --run-id <id>` CLI command with stdout and `--output` support.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `backtest-run-model`: Add human-readable report export behavior for persisted backtest results.
- `cli-database-initialization`: Expose backtest report export through the project CLI.

## Impact

- Code: add a core backtest report module and extend the CLI entrypoint.
- Tests: add core report formatter tests and CLI command tests.
- OpenSpec: update backtest persistence and CLI specs.
- No database migration is needed.
