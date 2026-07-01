## Why

The Signal Detail page currently shows latest signal metadata but does not expose the target holdings users need to inspect the generated allocation. COP-102 requires the page to display the real latest signal positions in a clear tabular form.

## What Changes

- Add a target holdings table to the Signal Detail page when the latest signal API returns `has_signal: true`.
- Render each position's exchange, symbol, target weight, rank, score, and fallback status from `GET /api/strategy-signals/latest`.
- Format decimal and percentage values clearly while preserving meaningful precision from API string fields.
- Keep the existing loading, empty, and API error states unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend the Signal Detail latest signal page requirement to include a real latest signal target holdings table.

## Impact

- Frontend page rendering in `apps/web/src/pages/SignalDetailPage.tsx`.
- Frontend styling in `apps/web/src/styles.css`.
- Frontend route tests in `apps/web/src/App.test.tsx`.
- OpenSpec `web-frontend-app` delta and archived spec.
