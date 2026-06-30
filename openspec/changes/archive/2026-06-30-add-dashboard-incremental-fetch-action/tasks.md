## 1. API Client

- [x] 1.1 Add typed shared client support for `POST /api/market-data/fetch?mode=incremental`.
- [x] 1.2 Add client tests covering the incremental fetch helper request path.

## 2. Dashboard Operation

- [x] 2.1 Enable the Dashboard market data fetch action to call the incremental fetch helper.
- [x] 2.2 Show an in-progress state and prevent duplicate fetch submissions while the operation is pending.
- [x] 2.3 Refresh Dashboard aggregate data after a successful incremental fetch.
- [x] 2.4 Show a concise operation failure state when the incremental fetch request fails.

## 3. Validation Coverage

- [x] 3.1 Add Dashboard interaction tests for click, loading state, duplicate prevention, and refresh.
- [x] 3.2 Extend local API integration validation so the frontend client can trigger the incremental fetch endpoint against a real local API.
- [x] 3.3 Run backend SQLite market data fetch integration validation to confirm `DataFetchLog` and `MarketPrice` persistence.

## 4. Final Checks

- [x] 4.1 Run relevant frontend tests, lint, typecheck, and build.
- [x] 4.2 Run relevant backend tests and project validation commands.
- [x] 4.3 Run OpenSpec validation for the change.
