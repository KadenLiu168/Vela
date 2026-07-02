## 1. Shared Test Data Setup

- [x] 1.1 Add a shared Python test-support module that initializes SQLite ORM tables and returns a session factory.
- [x] 1.2 Add deterministic helpers that seed active ETFs, market price history, latest signal rows, recent fetch logs, and backtest rows.
- [x] 1.3 Add a controlled market data provider helper for fetch endpoint integration tests.
- [x] 1.4 Add a CLI-accessible preparation path for local SQLite frontend/API acceptance setup.

## 2. Test Reuse

- [x] 2.1 Refactor API integration tests that duplicate SQLite setup to use the shared helpers.
- [x] 2.2 Add repository-level tests proving the shared setup initializes and seeds SQLite data.
- [x] 2.3 Keep frontend unit tests mocked, but ensure frontend API integration validation can target prepared backend state.

## 3. Documentation and Validation

- [x] 3.1 Document the frontend API integration preparation workflow and provider/persistence boundary.
- [x] 3.2 Run targeted API/data-preparation tests.
- [x] 3.3 Run full repository validation commands, frontend validation commands, and OpenSpec validation.
