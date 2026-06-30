## 1. Backend Aggregate Contract

- [x] 1.1 Add focused dashboard aggregation tests for latest successful signal selection, ignoring newer non-success signals, empty state when no successful signal exists, and fallback derivation from persisted positions.
- [x] 1.2 Update the dashboard aggregation latest signal summary to filter for `success` signals and include `is_fallback`.

## 2. API Integration Contract

- [x] 2.1 Extend the dashboard API SQLite integration test to verify latest successful signal selection and fallback status from persisted `StrategySignal` / `StrategySignalPosition` rows.
- [x] 2.2 Confirm the API response shape remains read-only and uses the existing dashboard aggregate path.

## 3. Frontend Dashboard

- [x] 3.1 Update dashboard API client types for the latest signal fallback field.
- [x] 3.2 Render signal date, result, fallback status, and target holding count in the Dashboard signal panel.
- [x] 3.3 Render a clear no-successful-signal empty state with a generate-signal entry point.
- [x] 3.4 Add frontend tests for populated signal summary, fallback status, and empty state entry point.

## 4. Validation

- [x] 4.1 Run focused backend/API/frontend tests for the dashboard signal summary behavior.
- [x] 4.2 Run available lint, type check, and OpenSpec validation commands.
- [x] 4.3 Review the final diff for scope, findings, and OpenSpec alignment.
