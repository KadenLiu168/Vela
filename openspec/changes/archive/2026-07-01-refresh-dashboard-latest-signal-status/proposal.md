## Why

After a signal is generated from the Dashboard, the Dashboard must immediately reflect the latest persisted signal state and stay consistent with the Signal Detail page. This closes the frontend loop across signal generation, Dashboard summary refresh, and persisted latest-signal reads.

## What Changes

- Update the Dashboard signal refresh flow so successful signal generation reloads both the Dashboard aggregate and the structured latest signal data.
- Ensure the Dashboard latest signal summary can be backfilled from the same persisted latest signal result used by the Signal Detail page.
- Add tests that verify Dashboard summary and Signal Detail display the same generated signal after a successful generation request and after browser refresh.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend Dashboard signal-generation behavior so the Dashboard backfills latest signal state from persisted backend data shared with the Signal Detail page.

## Impact

- Frontend Dashboard page state and tests in `apps/web`.
- Existing shared API client helpers for `GET /api/dashboard`, `POST /api/strategy-signals/generate`, and `GET /api/strategy-signals/latest`.
- OpenSpec `web-frontend-app` requirements.
- No backend API, database schema, or dependency changes.
