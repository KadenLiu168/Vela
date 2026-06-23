## Why

Users can generate and persist strategy signals, but they do not yet have a direct way to export the latest signal as a human-readable report. COP-54 needs a simple report surface for reviewing the latest selected ETFs, weights, scores, and fallback state.

## What Changes

- Add a core signal report helper that loads the latest successful strategy signal for a config version, optionally constrained by signal date.
- Format the latest signal as a human-readable text report containing signal date, config version, signal id, generated timestamp, selected ETFs, target weights, scores, and fallback status.
- Add a CLI command to export the latest signal report to stdout or a requested file path.
- Add focused core and CLI tests for successful reports, fallback reports, missing latest signals, and file export.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `strategy-signal-generation`: Add latest signal report export behavior for persisted strategy signals.
- `cli-database-initialization`: Add a CLI command for exporting the latest signal report from the local database.

## Impact

- Affected code: `packages/core/src/vela_core`, `apps/cli/src/vela_cli/main.py`.
- Affected tests: core strategy signal report tests and CLI export command tests.
- Affected specs: `strategy-signal-generation` and `cli-database-initialization`.
- No database schema changes, external dependencies, broker integrations, or web UI changes.
