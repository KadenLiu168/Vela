## Context

The full market-data fetch path is already complete end-to-end except for the UI entry point:

- Backend: `POST /api/market-data/fetch?mode=full` is implemented (`apps/api/src/vela_api/market_router.py:35-44`, branches to `fetch_full_market_prices`).
- Client: `fetchFullMarketData()` is defined (`apps/web/src/api/client.ts:490-494`) and already unit-tested (`apps/web/src/api/client.test.ts:336-342`).
- Handler: `DashboardPage.handleMarketDataFetch(mode)` already branches on `mode === "full"` to call `fetchFullMarketData()` (`apps/web/src/pages/DashboardPage.tsx:109`).
- State: `marketDataFetchMode` state and `setMarketDataFetchMode(mode)` already exist (`DashboardPage.tsx:70,105`).
- Pending feedback: `getOperationPendingMessage` already distinguishes full (`DashboardPage.tsx:938`).
- Fetch log: `DashboardFetchLogSummary.mode` is a free string (`client.ts:127`), so the Data fetches panel already displays full rows without change.

The single gap: the Operations action list has one fetch button whose `onClick` is hard-coded to `handleMarketDataFetch("incremental")` via `marketFetchAction.onClick` (`DashboardPage.tsx:212-218,374-381`). A latent bug at `DashboardPage.tsx:380` — the loading label only matches `marketDataFetchMode === "incremental"` — would render a static label (not "Fetching…") the moment full becomes reachable.

Constraints: pure frontend, zero backend changes, zero `client.ts` changes (the function already exists), reuse existing `MarketDataFetchSummary` / `OperationErrorSummary` / `activeOperation` lock, no new components.

## Goals / Non-Goals

**Goals:**
- Make full market-data fetch triggerable from the Dashboard UI, reusing the already-wired handler/client/state.
- Fix the loading-label bug at `DashboardPage.tsx:380` as a natural consequence of the UI change.
- Establish the first component-level test for `DashboardPage` to guard both fetch paths, the lock, and result rendering.

**Non-Goals:**
- No backend, `client.ts`, API type, or new-component changes.
- No confirmation dialog for full fetch (see Decisions).
- No change to the `EmptyAction` shown when `price_rows === 0` (see Open Questions).
- No change to fetch-log presentation (already mode-agnostic).
- No change to the CLI or to how `fetch_full_market_prices` behaves server-side.

## Decisions

### Decision 1: Two independent buttons, not a dropdown or a mode toggle

The Operations panel already renders a flat button list (`operation-list`, `DashboardPage.tsx:373-400`: Fetch market data / Generate signal / Bootstrap). Adding a second "Fetch full" button matches this existing pattern with zero layout restructuring.

- **Dropdown (select)**: rejected — introduces a form control plus keyboard/focus a11y management that is absent from this panel today; over-engineered for a binary choice.
- **Mode toggle + single button**: rejected — carries implicit state (the user must remember which mode is armed before clicking), and the button label must mutate with the mode, increasing cognitive load.
- **Two buttons**: each button is self-describing and stateless from the user's view; clicking either immediately fires that mode. Adopted.

### Decision 2: Full button uses the tertiary variant with a `title` hint, no confirmation dialog

Full re-fetch re-downloads all ETF price history and is heavier than incremental. To discourage accidental clicks without blocking the operation:

- Render "Fetch full" with `className="button-tertiary"` (visually de-emphasized relative to the secondary "Fetch market data" button), consistent with the project's three-variant button system already referenced by the `EmptyAction advertises its variant` requirement in `web-frontend-app`.
- Add `title="Re-downloads all ETF price history"` to disclose the cost on hover/focus.
- **No confirm dialog**: the backend full re-fetch is idempotent and non-destructive (it overwrites price rows but does not delete the database or strategy state), and the existing CLI `vela fetch --mode full` requires no confirmation. A dialog would be inconsistent and over-protective for a local research tool.

### Decision 3: Reuse the single `activeOperation` lock and `marketDataFetchMode` state

Both buttons share `activeOperation === "marketDataFetch"` as their in-flight marker and `marketDataFetchMode` as the single discriminator. Because `marketDataFetchMode` is a single value set at fetch start and cleared in `finally` (`DashboardPage.tsx:105,119`), only one fetch can be in flight at a time — exactly the existing concurrency contract. A new `fullFetchAction` object mirrors `marketFetchAction` (`isDisabled: hasActiveOperation`, `isLoading: activeOperation === "marketDataFetch"`, `onClick: () => handleMarketDataFetch("full")`). No new state is introduced.

### Decision 4: Per-button loading labels resolve the L380 bug

Today the single button's label is `{marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"}` (`DashboardPage.tsx:380`), which mis-renders for full. With two buttons, each button's label keys off whether `marketDataFetchMode` matches its own mode:

- Incremental button: `marketDataFetchMode === "incremental" ? "Fetching market data" : "Fetch market data"`
- Full button: `marketDataFetchMode === "full" ? "Fetching full market data" : "Fetch full"`

This fixes the bug structurally rather than patching the conditional, and keeps the `OperationPendingFeedback` copy (`DashboardPage.tsx:938`, already full-aware) as the canonical in-progress message.

### Decision 5: New `DashboardPage.test.tsx` is the test home

`DashboardPage` currently has no component test (confirmed: no `DashboardPage.test.tsx` exists under `apps/web/src/`). The new file uses `@testing-library/react` plus `vi.stubGlobal("fetch", ...)` — the same stubbing pattern already used in `apps/web/src/api/client.test.ts:312` — to assert the request URL and the rendered summary. `client.test.ts` already covers `fetchFullMarketData` → `?mode=full` at the client layer, so the component test focuses on the Dashboard's wiring (button → handler → client → summary), not on re-asserting client-layer behavior.

## Risks / Trade-offs

- **[Accidental full fetch wastes time]** → tertiary visual variant + `title` hint; no confirm dialog, matching CLI parity. Acceptable for a local research tool.
- **[Two buttons share one `marketDataFetchMode` value]** → this is intentional: the value is a single discriminator guarded by the `activeOperation` lock, so the two buttons can never both be in flight. No race.
- **[First component test for DashboardPage has no prior pattern in-repo for this page]** → reuse the `vi.stubGlobal("fetch")` pattern from `client.test.ts`; render with `MemoryRouter` only if routing is touched (it is not for the Operations panel).
- **[Loading-label fix changes existing button copy semantics]** → the incremental button's label is byte-identical to today when incremental is in flight or idle; only the previously-unreachable full path gets a correct label. No regression for the existing path.

## Open Questions

- **EmptyAction mode on first run**: the `EmptyAction` rendered when `price_rows === 0` (`DashboardPage.tsx:299-308`) reuses `marketFetchAction.onClick`, so it also fires incremental. Semantically, a first-time fetch on an empty database arguably should be full (incremental has no baseline to diff against), but the correct answer depends on `fetch_incremental_market_prices`'s behavior against an empty price table — a backend concern outside this change's scope. Left for a follow-up; this change does not alter `EmptyAction` wiring.
