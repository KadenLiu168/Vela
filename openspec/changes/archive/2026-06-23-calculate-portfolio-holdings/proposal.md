## Why

Backtesting needs a deterministic daily portfolio holding series derived from strategy signals before it can calculate equity curves or performance metrics. COP-57 adds that bridge by turning persisted rebalance signals into explicit date-by-date target holdings.

## What Changes

- Add a core backend capability to calculate portfolio holdings for a requested trading-date range from persisted successful strategy signals.
- Carry each rebalance signal's target weights forward until the next rebalance signal changes the portfolio.
- Support empty holdings before the first applicable signal and target weights sourced directly from signal positions, including equal-weight signals already produced by strategy generation.
- Keep the change in core business logic and tests; no CLI, API, database schema, or equity-curve calculation changes.

## Capabilities

### New Capabilities
- `portfolio-holdings`: Calculate daily portfolio target holdings from strategy signal positions over a trading-date range.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/core/src/vela_core/`, especially a new portfolio holding calculation helper and public exports.
- Affected tests: `packages/core/tests/` unit tests for daily and interval holdings.
- Affected specs: new OpenSpec capability under `openspec/changes/calculate-portfolio-holdings/specs/portfolio-holdings/spec.md`.
- Dependencies and storage: no new runtime dependencies and no database migration.
