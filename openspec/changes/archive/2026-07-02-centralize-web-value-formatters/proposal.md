## Why

Frontend pages currently format numbers, percentages, dates, Decimal strings, and nullable values with duplicated page-local helpers. This causes inconsistent empty-state labels and makes backtest metrics, signal holdings, target weights, scores, and dates harder to keep aligned.

## What Changes

- Add shared frontend formatting helpers for nullable values, ISO date/timestamp display, integer counts, Decimal strings, percentages, target weights, and net values.
- Replace page-local formatting in Dashboard, Signal Detail, and Backtest Detail with the shared helpers.
- Keep display behavior minimal and local to the web frontend; no API, backend, or data model changes.
- Add frontend tests that cover consistent formatting and nullable `n/a` states.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: Add requirements for centralized and consistent frontend value formatting.

## Impact

- Affected code: `apps/web/src` frontend pages and shared utility code.
- Affected tests: frontend rendering tests in `apps/web/src`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md`.
- No API contract, backend, database, or dependency changes.
