## Context

`GET /api/dashboard` already returns `market_data.price_rows`, `market_data.covered_etfs`, `market_data.earliest_trade_date`, and `market_data.latest_trade_date` from persisted SQLite `MarketPrice` rows. The Dashboard page already calls that endpoint through the shared frontend client and renders those values, but zero local prices are not called out as an explicit state.

## Goals / Non-Goals

**Goals:**

- Keep the Dashboard market panel backed by the existing typed `getDashboard()` client.
- Show populated market data with earliest date, latest date, record count, and ETF coverage.
- Show an explicit empty market data state when `price_rows` is `0`.
- Verify the UI state with frontend tests and rely on the existing API SQLite integration test for real persisted data validation.

**Non-Goals:**

- Do not change the dashboard API response shape.
- Do not add market data fetch actions or make the disabled operation buttons functional.
- Do not refactor Dashboard layout or unrelated Dashboard sections.

## Decisions

- Treat `price_rows === 0` as the empty market data condition.
  - Rationale: the aggregate API already reports zero rows and null date bounds for an empty `MarketPrice` table.
  - Alternative considered: infer emptiness from null date fields. That is less direct than the record count and could hide data quality issues if dates are unexpectedly missing.
- Keep the empty state inside the existing market data panel.
  - Rationale: users are already looking at that panel for market status; adding a separate global banner would expand scope and duplicate state.
- Do not add backend tests in this COP unless existing validation fails.
  - Rationale: `apps/api/tests/test_dashboard.py` already validates `/api/dashboard` against a temporary SQLite database containing persisted `MarketPrice`, `StrategySignal`, and `BacktestRun` rows.

## Risks / Trade-offs

- Empty state copy could become inconsistent with future enabled fetch actions -> Keep copy concise and tied to current guidance rather than button behavior.
- Frontend tests still mock `fetch` for UI rendering -> Pair them with the existing real FastAPI + SQLite integration test during validation.
