## 1. Model and migration

- [x] 1.1 Add failing model/migration tests: `data_snapshot_json` column exists (nullable SQLAlchemy `JSON`), `BacktestRun` exposes it, the required-column and nullable tests include it, downgrade removes it, and `compare_metadata` is clean at head.
- [x] 1.2 Add `data_snapshot_json: Mapped[dict[str, object] | None]` to `BacktestRun` (`models/backtest.py`) — use SQLAlchemy `JSON` type and `nullable=True`; do not add a mutable Python default.
- [x] 1.3 Add `data_snapshot_json: dict[str, object] | None = None` to `BacktestResultRunInput` (`backtest_result_persistence.py`), and wire it into `BacktestRun(...)` construction inside `persist_backtest_result`; update every existing test factory of that dataclass only as required by its final field order.
- [x] 1.4 Create Alembic migration adding the nullable JSON column; upgrade uses `op.add_column`, downgrade uses `op.batch_alter_table` wrapping `drop_column` (SQLite DROP COLUMN compatibility).
- [x] 1.5 Add a migration test covering upgrade/downgrade round-trip, JSON writability (insert a row with non-null `data_snapshot_json` at head), and `compare_metadata` clean after round-trip.

## 2. Snapshot computation in runner

- [x] 2.1 Add failing runner tests: `run_backtest` persists the computed `data_snapshot_json` without committing; its loaded panel and summary include an active-ETF row after the last rebalance date but on/before requested `end_date`; historical signal input remains truncated at each rebalance date; partial-status runs also persist the snapshot.
- [x] 2.2 Implement a snapshot-builder helper computing `min_trade_date`, `max_trade_date`, `trading_day_count`, `active_etf_count`, `per_etf_row_counts` (decimal-string ETF-id keys), and `data_checksum`. Feed sha256 a newline-delimited sequence of compact UTF-8 JSON arrays `[etf_id, trade_date.isoformat(), str(close_price), str(factor_hfq)]`, sorted by `(etf_id, trade_date)`; define the documented empty-panel summary.
- [x] 2.3 Wire the helper into `run_backtest` immediately after `load_price_panel`; load that panel from the existing lookback start through requested `end_date`, reuse it for equity-curve market-price input, pass the snapshot through `BacktestResultRunInput(data_snapshot_json=...)` to `persist_backtest_result`, and retain the existing per-rebalance date truncation in `generate_historical_strategy_signals`.

## 3. Checksum correctness

- [x] 3.1 Add checksum tests: identical panel → identical `data_checksum`; any single `close_price` or `factor_hfq` change → different checksum; row-order independence; differently segmented field values cannot collide because each row is structured JSON.
- [x] 3.2 Add snapshot-builder standalone unit tests: empty panel exact summary and empty-stream digest, single ETF, single trade date, and JSON round-trip preservation of `per_etf_row_counts` string keys.

## 4. Verification

- [x] 4.1 Run focused model/persistence/runner/migration tests, then `uv run --no-sync pytest`.
- [x] 4.2 Run the exact Python CI commands: `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, and `uv run --no-sync mypy --config-file pyproject.toml`.
- [x] 4.3 Run `openspec validate add-backtest-data-snapshot --strict` and `openspec status --change add-backtest-data-snapshot --json`; confirm all artifacts complete and tasks checked only after verification passes.
