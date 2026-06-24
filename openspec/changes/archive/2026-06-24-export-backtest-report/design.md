## Context

`run-backtest` persists a `BacktestRun` and related `BacktestEquityCurve` rows, and prints the run id. `get_backtest_result(session, run_id=...)` can load a specific run with ordered curve rows. The existing signal report exporter uses a small core report module plus a thin CLI wrapper; COP-66 follows the same pattern.

The user selected deterministic run-id export and a concise curve summary: metadata, core metrics, point count, first row, last row, min net value row, and max net value row.

## Goals / Non-Goals

**Goals:**

- Export a persisted backtest report by explicit run id.
- Produce stable, human-readable plain text.
- Support stdout and optional file output from the CLI.
- Fail clearly when the run id is missing.

**Non-Goals:**

- Do not run or recompute a backtest.
- Do not implement latest-run selection.
- Do not export full daily curve rows, CSV, JSON, charts, or rich documents.

## Decisions

1. Use explicit `run_id`.

   Rationale: Backtest history allows reruns for the same strategy and date range, so run id avoids ambiguous latest selection.

2. Keep report output plain text.

   Rationale: This matches the existing signal report and is sufficient for local acceptance and manual review.

3. Summarize the equity curve with first, last, min, and max rows.

   Rationale: These rows give enough context to verify date range, terminal value, and extrema without dumping a long daily series.

## Risks / Trade-offs

- Users need the run id -> `run-backtest` already prints it.
- Summary omits intermediate path -> Defer full curve export to a separate issue if needed.
- Empty curve results have no first/last/min/max rows -> Print a clear `none` summary.
