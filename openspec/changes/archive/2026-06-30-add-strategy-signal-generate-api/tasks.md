## 1. API Contract Tests

- [x] 1.1 Add API route surface tests for `POST /api/strategy-signals/generate`.
- [x] 1.2 Add integration coverage for omitted `signalDate` using the latest local `MarketPrice.trade_date`.
- [x] 1.3 Add integration coverage for explicit `signalDate`.
- [x] 1.4 Add failure coverage for omitted `signalDate` when no local market prices exist.

## 2. API Implementation

- [x] 2.1 Implement latest local market date lookup from SQLite.
- [x] 2.2 Wire `POST /api/strategy-signals/generate` to load the current strategy config and call `generate_strategy_signal`.
- [x] 2.3 Serialize signal id, signal date, config version, status, result, error message, and positions.

## 3. Validation

- [x] 3.1 Run focused API tests for strategy signal generation.
- [x] 3.2 Run project validation commands for tests, lint, type check where available, and OpenSpec status.
