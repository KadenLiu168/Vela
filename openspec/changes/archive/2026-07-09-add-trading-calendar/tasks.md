## 1. Model & migration

- [x] 1.1 Create `packages/core/src/vela_core/models/trading_calendar.py` with `TradingCalendar` ORM model: `trade_date` (Date, primary key), `source` (String, nullable=False), `created_at`, `updated_at` (DateTime, server_default=now, onupdate=now)
- [x] 1.2 Export `TradingCalendar` from `packages/core/src/vela_core/models/__init__.py`
- [x] 1.3 Create `alembic/versions/20260709_0009_create_trading_calendar.py` migration (down_revision = `20260709_0008`)
- [x] 1.4 Verify the new table appears via both DB init paths: fresh `create_all` and `alembic upgrade head`

## 2. Sync module

- [x] 2.1 Create `packages/core/src/vela_core/trading_calendar_sync.py` with `TradingCalendarSyncResult` frozen dataclass (`synced_count`, `inserted_count`, `updated_count`, `status`, `error_message`)
- [x] 2.2 Implement `sync_trading_calendar_to_db(session, *, source="akshare") -> TradingCalendarSyncResult`: call `import_module("akshare").tool_trade_date_hist_sina()`, parse the `trade_date` column, upsert via `insert.on_conflict_do_update` keyed on `trade_date`
- [x] 2.3 On akshare failure, return `failed` status with `error_message` instead of raising
- [x] 2.4 Export `TradingCalendarSyncResult` and `sync_trading_calendar_to_db` from `packages/core/src/vela_core/__init__.py`

## 3. CLI wiring

- [x] 3.1 Add `sync-trading-calendar` subparser with `--database-url` to `apps/cli/src/vela_cli/main.py` (mirror `sync-etf-pool`)
- [x] 3.2 Add `sync_trading_calendar(database_url)` wrapper + dispatch branch in CLI
- [x] 3.3 Print a sync summary (inserted/updated counts + status)

## 4. Unit tests for sync

- [x] 4.1 Create `packages/core/tests/test_trading_calendar_sync.py`
- [x] 4.2 Sync with a fake akshare module upserts trading days and reports correct counts
- [x] 4.3 Sync is idempotent: repeated runs produce no duplicates and update in place
- [x] 4.4 Sync failure (akshare raises) returns `failed` status with error message and does not raise
- [x] 4.5 `TradingCalendar` model exposes `trade_date` primary key and `source`/`created_at`/`updated_at` fields

## 5. CLI tests

- [x] 5.1 Extend `apps/cli/tests` to cover `sync-trading-calendar`: command invokes sync and prints a summary
- [x] 5.2 `sync-trading-calendar` returns nonzero on sync failure

## 6. Validation

- [x] 6.1 `ruff format` + `ruff check` pass
- [x] 6.2 `mypy` passes
- [x] 6.3 `pytest packages/core/tests apps/cli/tests` green
- [x] 6.4 `openspec validate --all` green
