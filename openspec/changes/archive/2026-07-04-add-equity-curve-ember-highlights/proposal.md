## Why

The Backtest Detail equity curve already uses Brass for the primary line, but Ember Orange is not yet present as the restrained chart punctuation described in `DESIGN.md`. Adding small highlight points makes the chart better match the data observatory visual language without changing its chart model.

## What Changes

- Add small Ember Orange circle highlights to multi-point equity curve charts.
- Keep the equity curve path and primary line styling in Brass.
- Reuse the existing SVG coordinate system and path geometry so the chart remains stable.
- Preserve current empty and single-point states without rendering a line path or highlight points.
- Add frontend tests for multi-point highlights and no-highlight edge states.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend Backtest Detail equity curve rendering with restrained Ember Orange highlight points for valid multi-point curves.

## Impact

- `apps/web/src/pages/BacktestDetailPage.tsx`
- `apps/web/src/styles.css`
- `apps/web/src/App.test.tsx`
- OpenSpec `web-frontend-app` delta spec
- No backend API, database, chart-library, or dependency changes
