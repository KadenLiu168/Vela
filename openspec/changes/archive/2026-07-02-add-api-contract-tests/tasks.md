## 1. API Contract Tests

- [x] 1.1 Add focused API contract tests for first-version success response structures across health, config, dashboard, market data fetch, strategy signal, and backtest endpoints.
- [x] 1.2 Add focused API contract tests for empty persistence states covering dashboard, latest signal, and backtest list responses.
- [x] 1.3 Add focused API contract tests for validation, not-found, missing market data, invalid date range, configuration, and provider workflow error paths.

## 2. Verification

- [x] 2.1 Reuse temporary SQLite setup and shared integration data helpers instead of endpoint-local schema setup where practical.
- [x] 2.2 Run targeted API tests and repository validation commands.
- [x] 2.3 Review this change against COP-121, the proposal, and delta specs before archive.
