## 1. Regression tests first

- [x] 1.1 In `packages/core/tests/test_strategy_signal_report.py`, add a failing regression with a
  newer successful `Other_strategy/v1` row and assert the report query returns the
  `Dual_momentum/v1` row; also assert a requested strategy with no successful row returns `None`.
- [x] 1.2 In `packages/core/tests/test_strategy_signal_persistence.py`, add a failing exact-date
  regression proving `get_latest_successful_strategy_signal` ignores a newer successful row for a
  different strategy sharing `"v1"`.
- [x] 1.3 In `packages/core/tests/test_portfolio_holdings.py`, add a failing regression proving
  latest-per-date holdings ignore a newer foreign-strategy row while preserving T+1 application.
- [x] 1.4 In `packages/core/tests/test_dashboard_aggregation.py`, use
  `strategy_id="Dual_momentum"` in `_strategy_summary`, update only the two full strategy-echo
  expectations that depend on it, and add a failing regression proving the Dashboard ignores a
  newer successful `Other_strategy/v1` row.
- [x] 1.5 Extend `apps/api/tests/test_strategy_signal_latest.py` with a newer successful
  `Other_strategy/v1` fixture and keep the expected response pinned to the configured
  `Dual_momentum/v1` signal.
- [x] 1.6 Add a focused CLI wrapper test in `apps/cli/tests/test_export_signal_report.py` that
  stubs `load_strategy_config` with a config carrying a distinctive id, replaces the core export
  helper with a spy, and asserts `export_signal_report` forwards both `strategy_id` and
  `config_version`.
- [x] 1.7 Run the targeted tests from 1.1–1.6 and confirm they fail for the missing strategy
  parameter/filter or caller wiring, not for fixture setup.

## 2. Core report and exact-date helpers

- [x] 2.1 Add a required keyword-only `strategy_id: str` to
  `_get_latest_successful_signal`, `get_latest_strategy_signal_report`, and
  `export_latest_strategy_signal_report`; forward it through the chain and filter the SQL query by
  exact `strategy_id + config_version`.
- [x] 2.2 Update every repository call to the report helpers, including the six existing calls in
  `packages/core/tests/test_strategy_signal_report.py`, to pass the matching strategy id.
- [x] 2.3 Add a required keyword-only `strategy_id: str` to
  `get_latest_successful_strategy_signal`, filter by exact `strategy_id + config_version`, and
  update every repository call in `packages/core/tests/test_strategy_signal_persistence.py`.
- [x] 2.4 Run the report and persistence test modules and confirm the new and existing cases pass.

## 3. Dashboard scoping

- [x] 3.1 In `get_dashboard_summary`, read the required `strategy_id` and `version` keys from
  `strategy_summary` and pass them to `_get_latest_signal_summary`.
- [x] 3.2 Add required keyword-only `strategy_id` and `config_version` parameters to
  `_get_latest_signal_summary` and filter its query by exact composite identity before ordering and
  limiting.
- [x] 3.3 Run the core Dashboard aggregation tests and the API Dashboard tests; confirm foreign
  rows are ignored and the response shape is unchanged.

## 4. Portfolio holdings and backtest propagation

- [x] 4.1 Add a required keyword-only `strategy_id: str` to
  `calculate_portfolio_holdings` and `_latest_successful_signals_by_date`, forward it, and filter
  latest-per-date selection by exact `strategy_id + config_version`.
- [x] 4.2 Update all direct repository callers and tests of `calculate_portfolio_holdings`.
- [x] 4.3 In `calculate_strategy_equity_curve`, pass
  `strategy_id=strategy_config.strategy_id`; in `run_backtest`, pass
  `strategy_id=config.strategy_id` to its direct holdings call.
- [x] 4.4 Update the affected `calculate_portfolio_holdings` test double in
  `test_backtest_runner.py`, then run the backtest-runner and strategy-equity-curve modules together
  with `test_portfolio_holdings.py`.

## 5. API and CLI wiring

- [x] 5.1 In API `latest_strategy_signal`, pass `strategy_id=config.strategy_id` alongside
  `config_version=config.version`.
- [x] 5.2 In CLI `export_signal_report`, pass `strategy_id=config.strategy_id` alongside
  `config_version=config.version`.
- [x] 5.3 Run `apps/api/tests/test_strategy_signal_latest.py`,
  `apps/api/tests/test_dashboard.py`, and `apps/cli/tests/test_export_signal_report.py`; confirm the
  discriminating caller-wiring regressions pass.

## 6. Repository-wide verification

- [x] 6.1 Use a repository-wide symbol search for the four changed public helpers and
  `calculate_portfolio_holdings`; confirm every caller and test double supplies `strategy_id`.
- [x] 6.2 Run the Python quality gates from the repository root:
  `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, and `uv run pytest`.
- [x] 6.3 Run `openspec validate fix-signal-latest-strategy-scoping` and confirm all artifacts pass.
- [x] 6.4 Review the final diff and confirm it contains no migration, frontend change, response
  shape change, report-format change, status/source semantic change, or unrelated refactor.
