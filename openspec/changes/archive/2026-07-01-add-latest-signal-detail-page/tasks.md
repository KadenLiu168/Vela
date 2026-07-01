## 1. API Client

- [x] 1.1 Add latest strategy signal response types to the shared frontend API client.
- [x] 1.2 Add a `getLatestStrategySignal` helper that calls `GET /api/strategy-signals/latest`.

## 2. Signal Detail Page

- [x] 2.1 Replace the Signal Detail placeholder with loading, error, empty, and populated latest signal states.
- [x] 2.2 Render signal date, config version, result, fallback status, and generated timestamp from the API response.
- [x] 2.3 Keep candidate ranking diagnostics out of the first version.

## 3. Tests and Validation

- [x] 3.1 Add API client tests for the latest signal helper.
- [x] 3.2 Add page tests for populated latest signal, empty latest signal, and API failure states.
- [x] 3.3 Run frontend tests, lint, type check, relevant full test suite, and OpenSpec validation.
