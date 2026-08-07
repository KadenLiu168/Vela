## Why

The backend `POST /api/market-data/fetch?mode=full` endpoint exists (`apps/api/src/vela_api/market_router.py:35`), the frontend client function `fetchFullMarketData()` is defined (`apps/web/src/api/client.ts:490`), and `DashboardPage.handleMarketDataFetch(mode)` already branches to the full path (`apps/web/src/pages/DashboardPage.tsx:109`). Despite this, the Dashboard's only fetch button hard-codes `"incremental"` (`DashboardPage.tsx:216`), so users can never trigger a full re-fetch from the UI — they must drop to the CLI after events like ex-dividend dates or data-source corrections. The handler, client, state, and pending-feedback copy are all already full-capable; the sole gap is a missing UI entry point, plus a latent loading-label bug that surfaces the moment full is reachable.

## What Changes

- Add a dedicated "Fetch full" button to the Dashboard Operations action list, wired to the existing `handleMarketDataFetch("full")` path. Use the tertiary button variant with a `title` hint that full re-downloads all ETF price history, so the heavy operation is visually distinguished from routine incremental fetches without blocking it behind a confirmation dialog (the backend full re-fetch is idempotent and non-destructive, matching CLI behavior).
- Add a `fullFetchAction` next to the existing `marketFetchAction`, reusing the shared `activeOperation` lock, `isDisabled`, and result/error surface — no new state, no new components.
- Fix the existing fetch button's loading label at `DashboardPage.tsx:380`, which only matches `marketDataFetchMode === "incremental"` and would render a static label (not "Fetching…") once full is reachable. With two independent buttons, each button owns its own loading label, resolving the bug as a natural consequence.
- Add the first component-level test for `DashboardPage` (`apps/web/src/pages/DashboardPage.test.tsx`), covering: full button issues `POST /api/market-data/fetch?mode=full`; incremental button preserves `?mode=incremental` (regression guard); the `activeOperation` lock disables the sibling action while one is in flight; `MarketDataFetchSummary` renders the response.
- No backend changes. No `client.ts` changes (`fetchFullMarketData` already exists and is already covered by `client.test.ts:336-342`). No new API functions, types, or components.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Add a Dashboard Operations requirement that exposes an independent full market-data fetch entry point, reusing the already-wired `handleMarketDataFetch("full")` path and `fetchFullMarketData` client function; the incremental path remains unchanged; the `activeOperation` lock and shared result/error surface are preserved.

## Impact

- **Code**: `apps/web/src/pages/DashboardPage.tsx` (new button + action object + loading-label fix); new `apps/web/src/pages/DashboardPage.test.tsx`.
- **APIs**: None. `POST /api/market-data/fetch?mode=full` is already implemented and unchanged.
- **Dependencies**: None.
- **Tests**: New component test file; existing `client.test.ts` incremental/full coverage is unchanged. Full Web gate (`lint`, `lint:css`, `typecheck`, `test`, `build`) must pass.
- **Out of scope**: The `EmptyAction` shown when `price_rows === 0` (`DashboardPage.tsx:299-308`) also reuses the incremental-wired `marketFetchAction.onClick`; whether a first-time empty-database fetch should default to full is a separate backend-behavior question and is recorded as an open question in `design.md`, not addressed by this change.
