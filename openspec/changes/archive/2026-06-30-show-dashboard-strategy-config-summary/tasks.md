## 1. Frontend Contract

- [x] 1.1 Tighten the dashboard strategy response TypeScript types for the configuration fields rendered by the Strategy panel.

## 2. Dashboard Rendering

- [x] 2.1 Expand the Dashboard Strategy panel to show strategy id/version, momentum windows, score weights, Top N, defensive asset, and transaction cost summary.
- [x] 2.2 Keep the Strategy panel read-only with no edit controls or configuration mutation entry point.

## 3. Tests

- [x] 3.1 Add frontend rendering coverage proving the Strategy panel displays the required configuration fields from the dashboard API response.
- [x] 3.2 Add frontend coverage proving no strategy configuration edit entry point is exposed.

## 4. Validation

- [x] 4.1 Run the focused frontend test suite for `apps/web`.
- [x] 4.2 Run frontend type check and lint scripts if available.
- [x] 4.3 Run OpenSpec status/validation for `show-dashboard-strategy-config-summary`.
