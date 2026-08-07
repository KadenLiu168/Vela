## 1. Dashboard UI wiring

- [x] 1.1 In `apps/web/src/pages/DashboardPage.tsx`, add a `fullFetchAction` object alongside `marketFetchAction` (around `DashboardPage.tsx:212`), with `isDisabled: hasActiveOperation`, `isLoading: activeOperation === "marketDataFetch"`, and `onClick: () => { void handleMarketDataFetch("full"); }`. No new state, no new `activeOperation` key.
- [x] 1.2 In the Operations `operation-list` (`DashboardPage.tsx:373`), render a second fetch button labeled "Fetch full" with `className="button-tertiary"`, `disabled={fullFetchAction.isDisabled}`, `onClick={fullFetchAction.onClick}`, and `title="Re-downloads all ETF price history"`. Place it immediately after the existing "Fetch market data" button.
- [x] 1.3 Fix the loading label at `DashboardPage.tsx:380`: the incremental button keeps `{marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"}`; the new full button uses `{marketDataFetchMode === "full" ? "Fetching full market data" : "Fetch full"}`. Do not change `OperationPendingFeedback` (already full-aware at `DashboardPage.tsx:938`).
- [x] 1.4 Leave the `EmptyAction` at `DashboardPage.tsx:299-308` unchanged (its mode is the Open Question in `design.md`).

## 2. Component tests

- [x] 2.1 Create `apps/web/src/pages/DashboardPage.test.tsx` using `@testing-library/react` and `vi.stubGlobal("fetch", ...)`, mirroring the stub pattern in `apps/web/src/api/client.test.ts:312`. Render `DashboardPage` with a stubbed `GET /api/dashboard` response so the Operations panel mounts.
- [x] 2.2 Assert that clicking the "Fetch full" button issues a `POST` to `/api/market-data/fetch?mode=full` (and not `mode=incremental`).
- [x] 2.3 Assert that clicking the "Fetch market data" (incremental) button issues `POST /api/market-data/fetch?mode=incremental` as a regression guard.
- [x] 2.4 Assert that while a fetch is in flight, the sibling fetch button is disabled and clicking it issues no second request.
- [x] 2.5 Assert per-button in-progress labels: incremental button shows its "Fetching market data" label only when `marketDataFetchMode === "incremental"`; full button shows "Fetching full market data" only when `marketDataFetchMode === "full"`.
- [x] 2.6 Assert that a successful `mode=full` response renders the shared `MarketDataFetchSummary` (e.g. the "Market data fetch success" heading and the Fetched/Inserted/Updated rows), and that a failed response renders `OperationErrorSummary` for the market-data-fetch operation.

## 3. Verification

- [x] 3.1 Run the full Web gate from the repo root: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, `npm --prefix apps/web run build`. All must pass.
- [x] 3.2 Run `openspec validate wire-full-market-data-fetch --strict` and confirm it passes.
