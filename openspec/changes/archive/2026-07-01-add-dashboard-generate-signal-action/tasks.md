## 1. Shared API Client

- [x] 1.1 Add typed response data for strategy signal generation.
- [x] 1.2 Add a `generateStrategySignal` helper that posts to `/strategy-signals/generate`.
- [x] 1.3 Add unit coverage for the shared client helper.

## 2. Dashboard Interaction

- [x] 2.1 Enable Dashboard generate-signal controls from the signal panel and operations panel.
- [x] 2.2 Show signal-generation loading state and prevent duplicate signal submissions.
- [x] 2.3 Reload Dashboard aggregate data after successful signal generation.
- [x] 2.4 Show a concise operation error when signal generation fails.

## 3. Validation Coverage

- [x] 3.1 Add Dashboard interaction tests for success, loading, refresh, and duplicate prevention.
- [x] 3.2 Add Dashboard interaction tests for signal-generation failure.
- [x] 3.3 Add opt-in local API integration validation for `POST /api/strategy-signals/generate`.

## 4. Verification

- [x] 4.1 Run focused frontend tests for the changed client and Dashboard behavior.
- [x] 4.2 Run frontend typecheck, lint, and full frontend tests.
- [x] 4.3 Run relevant backend signal generation API tests.
- [x] 4.4 Run OpenSpec validation.
