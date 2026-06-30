## 1. API Contract Tests

- [x] 1.1 Add API tests for incremental and full market data fetch modes.
- [x] 1.2 Add API validation coverage for invalid fetch mode.
- [x] 1.3 Add an integration test using temporary SQLite plus a controlled provider to prove rows and fetch logs are persisted through the real workflow.

## 2. API Implementation

- [x] 2.1 Add a FastAPI provider dependency that returns the production market data provider.
- [x] 2.2 Add `POST /api/market-data/fetch` with `mode=incremental|full` validation.
- [x] 2.3 Serialize the core fetch result with status, requested ETF count, row counts, failed symbols, and error message.

## 3. Validation

- [x] 3.1 Run focused API tests for the market data fetch endpoint.
- [x] 3.2 Run relevant project checks and OpenSpec validation.
