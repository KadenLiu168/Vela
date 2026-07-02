## Why

Dashboard and detail pages already call the real frontend API, but loading and operation feedback are still inconsistent across page data loads and long-running actions. COP-115 needs a unified first-phase frontend feedback layer so users can see what is happening, avoid duplicate submissions, and understand whether market data fetches, signal generation, and backtest runs completed successfully or failed.

## What Changes

- Add shared frontend feedback primitives for page loading, operation loading, success, and failure states.
- Update Dashboard actions so market data fetch, signal generation, and backtest run operations expose clear pending labels and prevent conflicting submissions while any operation is pending.
- Keep successful and failed operation results visible in the Operations panel after each operation completes.
- Update Signal Detail and Backtest Detail loading states to use the same page-loading feedback pattern as Dashboard.
- Add focused frontend tests for page loading, action pending states, duplicate/concurrent operation prevention, and success/failure feedback.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add consistent frontend loading and operation feedback requirements for page data loads and Dashboard actions.

## Impact

- Frontend only: `apps/web/src` React pages, shared components or styles, and tests.
- OpenSpec: extends `web-frontend-app`.
- API contracts: no request or response shape changes.
- Dependencies: no new runtime or development dependencies.
