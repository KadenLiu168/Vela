## 1. Tests

- [x] 1.1 Add API client tests for the typed dashboard aggregate helper.
- [x] 1.2 Add Dashboard route tests for successful aggregate rendering, empty latest signal/backtest data, and API failure state.

## 2. API Client

- [x] 2.1 Add TypeScript dashboard response types matching `GET /api/dashboard`.
- [x] 2.2 Add a shared `getDashboard()` helper that calls `/dashboard` through `apiRequest`.

## 3. Dashboard Page

- [x] 3.1 Replace the placeholder health check with dashboard aggregate loading.
- [x] 3.2 Render market status, strategy summary, latest signal, recent backtest, and operation sections.
- [x] 3.3 Add clear loading, error, and empty-data states.

## 4. Styling

- [x] 4.1 Update CSS for a dense local research dashboard layout without new dependencies.

## 5. Validation

- [x] 5.1 Run focused frontend tests for Dashboard and API client.
- [x] 5.2 Run applicable frontend lint, typecheck, build, and OpenSpec validation commands.
