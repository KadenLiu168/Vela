## 1. Model Tests

- [x] 1.1 Add tests that `MarketPrice` exposes the required daily OHLCV columns, nullable `adjusted_close`, and ETF foreign key.
- [x] 1.2 Add tests that duplicate `(etf_id, trade_date)` rows are rejected and same-date rows for different ETFs are allowed.
- [x] 1.3 Add tests that market price indexes support ETF/date and trade-date lookup paths.
- [x] 1.4 Add tests for the strategy price selection rule: use `adjusted_close` when present and `close_price` when it is null.

## 2. ORM Model

- [x] 2.1 Add a `MarketPrice` ORM model with `etf_id`, `trade_date`, OHLCV fields, nullable `adjusted_close`, and timestamps.
- [x] 2.2 Add the `(etf_id, trade_date)` unique constraint for de-duplication and future upsert conflict targeting.
- [x] 2.3 Add lookup indexes for ETF/date and trade-date query paths.
- [x] 2.4 Expose `MarketPrice` through `vela_core.models` so Alembic metadata discovery includes the table.

## 3. Migration

- [x] 3.1 Add an Alembic migration that creates `market_price` after `etf_info`.
- [x] 3.2 Include the ETF foreign key, unique constraint, and lookup indexes in the migration.
- [x] 3.3 Ensure the downgrade drops market price indexes and table cleanly.

## 4. Verification

- [x] 4.1 Run `openspec status --change "define-market-price-model"` and confirm the change is apply-ready.
- [x] 4.2 Run `uv run pytest packages/core/tests`.
- [x] 4.3 Run `uv run ruff check .`.
- [x] 4.4 Run `uv run mypy packages/core/src`.
- [x] 4.5 Run OpenSpec validation for the change.
