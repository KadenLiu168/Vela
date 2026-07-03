## Why

COP-125 requires validation that Dashboard-triggered signal generation reaches the backend workflow, persists `StrategySignal` and positions, and is then readable by both Dashboard and Signal Detail data sources. Existing tests cover generation, latest signal reads, and frontend rendering separately, but they do not prove the generated signal flows through all API reads in one closed loop.

## What Changes

- Add an API integration test that posts to the signal generation endpoint and then reads both the latest signal endpoint and Dashboard endpoint from the same temporary SQLite database.
- Verify the generated `StrategySignal` and `StrategySignalPosition` rows are persisted.
- Verify the latest signal API and Dashboard latest signal summary identify the same generated signal and position count.
- Keep frontend behavior unchanged because existing Dashboard and Signal Detail tests already verify rendering from the shared API responses.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `http-api-service`: Require a closed-loop validation that signal generation persistence is visible through both latest signal and Dashboard API reads.
- `test-suite-validation`: Require pytest coverage for the COP-125 signal generation to display data-source loop.

## Impact

- Affected tests: `apps/api/tests/test_strategy_signal_generate.py`
- Affected OpenSpec files: `http-api-service`, `test-suite-validation`
- No API contract changes.
- No new dependencies.
