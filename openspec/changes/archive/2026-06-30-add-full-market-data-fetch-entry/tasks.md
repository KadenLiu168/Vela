## 1. API Client

- [x] 1.1 Add a shared frontend API helper for `POST /api/market-data/fetch?mode=full`.
- [x] 1.2 Add a frontend API client unit test proving the full fetch helper uses the existing response contract.

## 2. Dashboard Entry Point

- [x] 2.1 Add a secondary Dashboard full fetch action after the incremental fetch action.
- [x] 2.2 Reuse the existing market data fetch summary for full fetch responses.
- [x] 2.3 Add Dashboard tests for full fetch request behavior, duplicate-submission prevention, lower priority ordering, and summary rendering.

## 3. Validation

- [x] 3.1 Extend the opt-in frontend local API integration test to call full fetch against the real API response contract.
- [x] 3.2 Run the relevant frontend tests and OpenSpec validation for this change.
