## 1. Model Tests

- [x] 1.1 Add tests that `DataFetchLog` exposes the required fetch task columns and nullable optional fields.
- [x] 1.2 Add tests that `DataFetchLog` supports `running`, `success`, `failed`, and `partial` status values.
- [x] 1.3 Add tests that full and incremental fetch logs can record source, target type, date range, requested symbols, result counts, and error messages.
- [x] 1.4 Add tests that data fetch log indexes support source/status/start-time and target/mode/range lookup paths.

## 2. ORM Model

- [x] 2.1 Add a `DataFetchLog` ORM model with task scope, lifecycle timestamp, status, count, error, and audit timestamp fields.
- [x] 2.2 Use SQLite-compatible column types, including text storage for serialized requested symbols and string storage for status and fetch mode.
- [x] 2.3 Add lookup indexes for source/status/start-time and target/mode/range query paths.
- [x] 2.4 Expose `DataFetchLog` through `vela_core.models` so Alembic metadata discovery includes the table.

## 3. Migration

- [x] 3.1 Add an Alembic migration that creates `data_fetch_log` after `market_price`.
- [x] 3.2 Include required columns, nullable optional columns, and lookup indexes in the migration.
- [x] 3.3 Ensure the downgrade drops data fetch log indexes and table cleanly.

## 4. Verification

- [x] 4.1 Run `openspec status --change "define-data-fetch-log-model"` and confirm the change is apply-ready.
- [x] 4.2 Run `uv run pytest packages/core/tests`.
- [x] 4.3 Run `uv run ruff check .`.
- [x] 4.4 Run `uv run mypy packages/core/src`.
- [x] 4.5 Run OpenSpec validation for the change.
