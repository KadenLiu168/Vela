## 1. Dashboard Summary UI

- [x] 1.1 Store the latest market data fetch API response in Dashboard state after a completed fetch.
- [x] 1.2 Render fetched, inserted, and updated row counts for successful fetch responses.
- [x] 1.3 Render failed symbols, error summaries, and retry/source/local data guidance for `partial` and `failed` fetch responses.
- [x] 1.4 Keep HTTP/network operation errors separate from workflow result summaries.

## 2. Validation Coverage

- [x] 2.1 Add Dashboard tests for successful fetch count summary rendering.
- [x] 2.2 Add Dashboard tests for `partial` response failed symbol and guidance rendering.
- [x] 2.3 Add Dashboard tests for `failed` response failed symbol and guidance rendering.
- [x] 2.4 Confirm the existing local API integration validation exercises the real fetch response contract used by the summary.

## 3. Final Checks

- [x] 3.1 Run focused frontend tests for Dashboard and API client behavior.
- [x] 3.2 Run project frontend lint, typecheck, and build commands.
- [x] 3.3 Run relevant backend API tests that prove the real fetch response contract.
- [x] 3.4 Run OpenSpec validation for the change.
