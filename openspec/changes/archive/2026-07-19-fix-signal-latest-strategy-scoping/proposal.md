## Why

Several reads choose the latest successful `StrategySignal` using `config_version` without
`strategy_id`. `config_version` is a low-entropy label such as `"v1"`, not a globally unique
strategy identity. When two strategies share a version label, these queries can return positions
from the wrong strategy:

- `GET /api/strategy-signals/latest` and the CLI report export share
  `get_latest_strategy_signal_report`, whose query filters by `config_version` only.
- The Dashboard latest-signal summary filters by neither strategy field.
- The public exact-date helper `get_latest_successful_strategy_signal` filters by
  `signal_date + config_version` only.
- Portfolio-holdings reconstruction, used directly by backtests and indirectly by equity-curve
  calculation, chooses the latest successful signal per date using `config_version` only.

The sibling signal-history list and detail HTTP endpoints already enforce the current
`strategy_id + config_version`, and `strategy_signal` already stores both fields. The fix makes
every current code path that selects a latest successful signal use the same composite strategy
identity.

## What Changes

- Require `strategy_id` in the report helper chain and filter the underlying latest-signal query
  by exact `strategy_id + config_version`.
- Pass the configured strategy id from the API latest endpoint and CLI export command.
- Scope the Dashboard latest successful signal to the `strategy_id` and `version` already present
  in its `strategy_summary` input.
- Require `strategy_id` in `get_latest_successful_strategy_signal` and filter its exact-date query
  by `strategy_id + config_version`.
- Require `strategy_id` in `calculate_portfolio_holdings`, propagate it through equity-curve and
  backtest callers, and scope latest-per-date selection by `strategy_id + config_version`.
- Add regression tests in each independently implemented or wired path. Every regression fixture
  includes a newer successful row for another strategy with the same `"v1"` version so the test
  fails if the strategy filter or caller wiring is missing.

HTTP response bodies, CLI output text, stored data, and frontend types do not change. Selection may
change for databases that already contain same-version rows from multiple strategies; that is the
intended correction.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `http-api-service`: Scope `GET /api/strategy-signals/latest` to the current `strategy_id` and
  `config_version`.
- `dashboard-aggregation`: Scope the Dashboard latest signal summary to the current
  `strategy_id` and `config_version`.
- `strategy-signal-generation`: Scope the core latest report helper to a supplied `strategy_id`
  and `config_version`.
- `cli-database-initialization`: Make `export-signal-report` use both identity fields loaded from
  its strategy config.
- `strategy-signal-model`: Scope the public exact-date latest-successful query helper to
  `strategy_id + config_version`.
- `portfolio-holdings`: Scope latest-per-date signal selection to
  `strategy_id + config_version`.

## Impact

- Core implementation:
  - `packages/core/src/vela_core/strategy_signal_report.py`
  - `packages/core/src/vela_core/strategy_signal_persistence.py`
  - `packages/core/src/vela_core/dashboard_aggregation.py`
  - `packages/core/src/vela_core/portfolio_holdings.py`
  - `packages/core/src/vela_core/strategy_equity_curve.py`
  - `packages/core/src/vela_core/backtest_runner.py`
- Application callers:
  - `apps/api/src/vela_api/main.py`
  - `apps/cli/src/vela_cli/main.py`
- Tests for the affected helpers and application wiring under `packages/core/tests`,
  `apps/api/tests`, and `apps/cli/tests`.
- The required `strategy_id` parameters are a breaking Python-call signature change for the
  helpers exported by `vela_core`. All in-repository callers are updated atomically. Vela is a
  local `0.1.0` application and has no declared third-party package compatibility contract; any
  untracked external Python caller must add the strategy id explicitly.
- No database migration and no frontend change.
