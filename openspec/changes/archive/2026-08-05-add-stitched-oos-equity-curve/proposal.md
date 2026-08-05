## Why

Walk-forward evaluation currently exposes each selected OOS window only as an isolated backtest, so users cannot see the cumulative return or capital path produced by compounding the realized OOS segments in chronological order. The existing specification also expressly forbids a continuous curve, which now needs a narrow, evidence-preserving replacement rather than an ambiguous visual-only join.

## What Changes

- Derive one deterministic stitched OOS equity curve from the persisted successful OOS backtest curves, preserving chronological window ownership and compounding each segment from the preceding segment's ending capital.
- Define boundary semantics explicitly: later OOS segments restart their strategy state at their own initial point, contribute no invented return or turnover at the seam, and are stitched only when the persisted official-session manifest proves that windows are adjacent and non-overlapping; valid gap/overlap configurations retain complete detail with an explicit unavailable status instead of a misleading curve.
- Expose the stitched points, ending net value, and cumulative total return in Walk-forward detail responses without duplicating curve data or adding a database migration.
- Present the curve and cumulative result on Walk-forward Detail with visible window-reset semantics and without claiming one continuously held or directly tradable portfolio.
- Replace the current blanket prohibition on linked OOS curves while retaining the prohibition on fabricated boundary returns, cross-window holdings continuity, and unrequested cross-window risk metrics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `walk-forward-runner`: Replace the isolated-curve prohibition with a deterministic continuous-compounding contract over adjacent persisted OOS segments, including validation and reset-boundary semantics.
- `http-api-service`: Extend Walk-forward detail with a typed stitched OOS curve/cumulative-return result or an explicit non-contiguous-window unavailable status derived from authoritative persisted evidence.
- `web-frontend-app`: Render the stitched OOS capital path when available, preserve complete detail when windows are non-contiguous, and clearly disclose window resets and the absence of synthesized seam returns or turnover.

## Impact

- Core Walk-forward query/derivation code and focused unit/integration tests under `packages/core`.
- `GET /api/walk-forwards/{run_id}` response schemas, eager loading, serialization, OpenAPI coverage, and API tests.
- Walk-forward frontend API types, detail presentation, chart behavior, responsive/accessibility coverage, and Web tests.
- Existing persisted Walk-forward and backtest records remain the source of truth; no schema migration, backfill, CLI execution change, dependency addition, or write to `vela.db` is required.
