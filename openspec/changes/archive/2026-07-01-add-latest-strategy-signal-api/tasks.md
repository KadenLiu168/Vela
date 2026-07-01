## 1. Core Read Model

- [x] 1.1 Extract or add reusable core logic that returns the latest successful strategy signal as structured metadata and positions.
- [x] 1.2 Preserve fallback detection and position ordering from existing strategy signal report behavior.

## 2. API Endpoint

- [x] 2.1 Add `GET /api/strategy-signals/latest` as a read-only FastAPI endpoint.
- [x] 2.2 Return `has_signal: true` with structured signal metadata and positions when a successful signal exists.
- [x] 2.3 Return `has_signal: false`, `signal: null`, and `positions: []` with `200 OK` when no successful signal exists.

## 3. Validation

- [x] 3.1 Add API integration tests using real `StrategySignal`, `StrategySignalPosition`, and `ETFInfo` rows.
- [x] 3.2 Add or adjust core tests for the structured latest signal read model.
- [x] 3.3 Run focused tests, feasible full tests, lint/type checks where available, and OpenSpec validation.
