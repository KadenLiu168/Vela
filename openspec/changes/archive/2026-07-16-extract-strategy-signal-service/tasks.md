## 1. Core Service

- [x] 1.1 Add `packages/core/src/vela_core/strategy_signal_service.py` with `generate_and_persist_strategy_signal(session, *, config, signal_date=None)`.
- [x] 1.2 Implement latest local market date resolution and raise `ValueError("No local market prices found")` when no date can be resolved.
- [x] 1.3 Move active ETF loading, price panel loading, defensive lookup construction, persistence callback construction, and position input conversion into the core service.
- [x] 1.4 Preserve explicit commit after signal persistence to match current API and CLI behavior.
- [x] 1.5 Export `generate_and_persist_strategy_signal` from `packages/core/src/vela_core/__init__.py`.

## 2. Core Tests

- [x] 2.1 Add core service tests for using the latest local market date when `signal_date` is omitted.
- [x] 2.2 Add core service tests for preserving an explicit `signal_date`.
- [x] 2.3 Add core service tests for missing local market prices raising `ValueError` and not persisting a signal.
- [x] 2.4 Add core service tests that successful generation persists the signal row and positions and returns the persisted signal id.
- [x] 2.5 Add or preserve tests proving the pure `generate_strategy_signal` entry point remains session-free and query-free.

## 3. Entrypoint Refactor

- [x] 3.1 Update `apps/api/src/vela_api/main.py` so `POST /api/strategy-signals/generate` calls the core service and only handles HTTP parameter parsing, error mapping, and response formatting.
- [x] 3.2 Update `apps/cli/src/vela_cli/main.py` so `generate_signal(...)` loads config, opens the managed session, calls the core service, and keeps existing CLI output/status behavior.
- [x] 3.3 Remove now-unused API and CLI imports for duplicated signal workflow internals.

## 4. Verification

- [x] 4.1 Run focused core strategy signal tests.
- [x] 4.2 Run API strategy signal generate tests.
- [x] 4.3 Run CLI generate-signal tests.
- [x] 4.4 Run OpenSpec validation/status checks for `extract-strategy-signal-service`.
