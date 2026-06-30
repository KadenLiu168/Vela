## Context

The dashboard aggregate API already returns `latest_signal`, and the frontend Dashboard already renders a signal panel. The backend summary currently selects the newest signal row by generation timestamp without filtering for successful signals, and the API payload does not expose whether the signal represents defensive fallback. Existing signal report code treats a position with no rank and no score as fallback, which matches how defensive fallback signals are persisted.

## Goals / Non-Goals

**Goals:**

- Summarize the latest successful persisted signal in the dashboard aggregate.
- Expose fallback status as a derived boolean on the latest signal summary.
- Render signal date, result, fallback status, and target holding count in the Dashboard.
- Provide a clear empty state with a generate-signal entry point when no successful signal exists.
- Validate with persisted `StrategySignal` / `StrategySignalPosition` data through the API path.

**Non-Goals:**

- Add a signal detail holdings table.
- Add signal generation execution from the web UI.
- Change the strategy signal database schema.
- Add new API endpoints.

## Decisions

1. Derive fallback status from persisted positions.
   - Rationale: Existing signal report behavior already marks fallback when a position has `rank is None` and `score is None`, and defensive fallback generation persists exactly that shape.
   - Alternative considered: add a new `is_fallback` column to `StrategySignal`. That would require a migration and duplicate data already represented by positions.

2. Select the latest successful signal in dashboard aggregation.
   - Rationale: COP-90 asks for the latest successful signal summary. Failed or running rows are useful audit history but should not replace the latest usable Dashboard signal.
   - Alternative considered: keep latest row regardless of status and show status. That conflicts with the acceptance criterion and can hide a valid successful signal behind a newer failure.

3. Keep the Dashboard action as a disabled entry point.
   - Rationale: Existing operations buttons are disabled placeholders. COP-90 only requires an entry point when no signal exists, not an executable signal-generation flow.
   - Alternative considered: wire the button to a generation API call. No such web API exists yet and that would exceed the first-stage frontend scope.

## Risks / Trade-offs

- Existing consumers of `GET /api/dashboard` may need to handle the new `is_fallback` field -> Mitigation: this is an additive response field and frontend client types will be updated together.
- Fallback derivation depends on persisted position shape -> Mitigation: the behavior matches the established report implementation and signal generation tests.
- Empty state action is not executable yet -> Mitigation: keep it visibly disabled and scoped as an entry point until a later issue adds execution.
