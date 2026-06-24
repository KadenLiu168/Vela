## 1. Core Backtest Runner

- [x] 1.1 Add a core backtest runner result dataclass.
- [x] 1.2 Query ordered local trading dates from `MarketPrice` for an inclusive date range.
- [x] 1.3 Generate historical strategy signals, calculate equity curve and metrics, and persist the backtest result.
- [x] 1.4 Map equity curve points and portfolio holdings to normalized `BacktestEquityCurveInput` rows.
- [x] 1.5 Export the runner result type and `run_backtest` from `vela_core`.

## 2. CLI Command

- [x] 2.1 Add `run-backtest` parser arguments for database URL, strategy config path, start date, and end date.
- [x] 2.2 Add CLI wrapper that loads config, opens a managed session, invokes the core runner, and handles errors.
- [x] 2.3 Print persisted run id and core metrics summary on success.

## 3. Tests

- [x] 3.1 Add core runner tests for trading date selection, metric persistence, normalized curve rows, and empty date failure.
- [x] 3.2 Add CLI tests for argument forwarding, default inputs, success summary, and failure exit.

## 4. Verification

- [x] 4.1 Run targeted core and CLI tests.
- [x] 4.2 Run full tests, lint, type check, and OpenSpec validation.
