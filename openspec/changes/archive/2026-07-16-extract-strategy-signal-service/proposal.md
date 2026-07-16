## Why

Strategy signal generation currently duplicates the same persistence orchestration in both the HTTP API endpoint and the CLI command. This leaks core business workflow into transport entrypoints, making future changes to signal persistence, ETF selection, or price-panel loading easy to apply in one path but miss in the other.

## What Changes

- Add a core-level strategy signal application service that generates and persists one strategy signal from a SQLAlchemy session, loaded strategy config, and optional signal date.
- Keep `generate_strategy_signal` as the pure injected-input strategy calculation function.
- Update the HTTP API generate endpoint to delegate signal generation/persistence orchestration to core and keep only request parameter handling, error mapping, and response formatting.
- Update the CLI `generate-signal` flow to delegate signal generation/persistence orchestration to core while retaining database URL, config path, and stdout/stderr handling.
- Remove duplicated API/CLI orchestration for active ETF loading, price panel loading, defense lookup construction, persistence callback construction, and signal persistence input conversion.
- No breaking changes to public HTTP response shape, CLI arguments, CLI output, persisted database schema, or strategy result semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `strategy-signal-generation`: Add a requirement that single-date strategy signal generation with persistence is orchestrated by core, so API and CLI paths share the same behavior.
- `http-api-service`: Clarify that the HTTP generate-signal endpoint delegates business orchestration to core while preserving existing API behavior.

## Impact

- Affected code:
  - `packages/core/src/vela_core/strategy_signal_generation.py` or a new core service module for orchestration.
  - `packages/core/src/vela_core/__init__.py` for public export.
  - `apps/api/src/vela_api/main.py` for endpoint simplification and import cleanup.
  - `apps/cli/src/vela_cli/main.py` for CLI wrapper simplification and import cleanup.
- Affected tests:
  - Add core service tests for latest-date resolution, explicit-date behavior, persistence, and missing-market-data errors.
  - Keep existing API and CLI contract tests passing.
- No database migration, dependency, or external integration changes are expected.
