## Why

The Dashboard exposes a "Full fetch for initialization or repair" button that calls `POST /api/market-data/fetch?mode=full`, but the label oversells what the endpoint actually does. The endpoint only re-fetches market prices; it does not run Alembic migrations, and it fails with "No active ETFs found" when the ETF metadata table is empty. A developer setting up Vela locally still has to run `uv run vela init-db` and `uv run vela sync-etf-pool` by hand before the Dashboard button is useful.

The Dashboard "Setup / bootstrap" action should run the three setup steps in order (migrate -> sync ETF pool -> full market data fetch) so a single click takes a fresh local database to a fully populated state.

## What Changes

- Add a `POST /api/setup/bootstrap` endpoint that runs the existing `init-db`, `sync-etf-pool`, and full market data fetch workflows in sequence.
- Add a reusable core orchestration function `run_local_setup_bootstrap` that the endpoint calls.
- Cache the loaded strategy config in API application state at startup so the bootstrap endpoint does not have to reload configuration or accept it from the caller.
- Replace the Dashboard "Full fetch for initialization or repair" button with a "Bootstrap / Setup database & data" button that targets the new endpoint, rendered in the primary (filled) variant and placed at the right end of the action list.
- Show a three-step status display (Migrate, Sync ETF pool, Fetch full market data) while the bootstrap runs and a final total duration after it finishes.
- Stop on the first failed step and report which step failed; do not roll back earlier successful steps.

## Capabilities

### New Capabilities

- `local-setup-bootstrap`: Defines the compound local-setup bootstrap operation, its per-step status response, hard-stop failure semantics, and local-development scope.

### Modified Capabilities

- `http-api-service`: Expose `POST /api/setup/bootstrap` and cache the loaded strategy config on application state.
- `web-frontend-app`: Replace the existing "Full fetch" Dashboard button with a bootstrap action that renders a three-step status display.

## Impact

- New API route: `apps/api/src/vela_api/main.py` adds `POST /api/setup/bootstrap`.
- New core module: `packages/core/src/vela_core/bootstrap.py` adds `run_local_setup_bootstrap` and result dataclasses.
- API startup wiring: `apps/api/src/vela_api/main.py` (or a new startup module) caches the loaded strategy config in `app.state` so the new endpoint reuses the same config that `/api/config` already serves.
- Dashboard: `apps/web/src/pages/DashboardPage.tsx` replaces the "Full fetch for initialization or repair" button, integrates `bootstrapLocalDatabase` from the API client, and renders the three-step status UI.
- Web styles: `apps/web/src/styles/buttons.css` (or equivalent) adds a primary (filled) button variant for the bootstrap action.
- API client: `apps/web/src/api/client.ts` adds `bootstrapLocalDatabase()`.
- Core tests: new tests for the orchestration module (success path, per-step failure, idempotent re-run).
- API tests: new tests for the endpoint, including failure isolation per step.
- Web tests: new tests for the bootstrap button and three-step status UI.
- No schema migrations and no new third-party dependencies.
