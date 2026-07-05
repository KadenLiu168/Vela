## 1. Core Tests

- [x] 1.1 Add core tests for `run_local_setup_bootstrap` that all three steps succeed end-to-end against an in-memory SQLite + fake provider.
- [x] 1.2 Add core tests for `run_local_setup_bootstrap` that step 2 (`sync_etf_pool`) failure aborts before step 3.
- [x] 1.3 Add core tests for `run_local_setup_bootstrap` that step 3 (`fetch_full_market_data`) failure still records the earlier successful step results.
- [x] 1.4 Add core tests that re-running `run_local_setup_bootstrap` against an already-initialized database reports each step as a no-op success.
- [x] 1.5 Add core tests that the result exposes per-step duration and total duration as floats.

## 2. Core Implementation

- [x] 2.1 Add `packages/core/src/vela_core/bootstrap.py` with `BootstrapStepResult` and `BootstrapResult` dataclasses.
- [x] 2.2 Implement `run_local_setup_bootstrap(session, provider, *, strategy_config, script_location)` that runs Alembic upgrade, then `sync_etf_pool_to_db`, then `fetch_full_market_prices`, capturing per-step status and duration.
- [x] 2.3 Stop the orchestrator on the first step whose `status` is not `success` and return the accumulated step results plus the failing step name.
- [x] 2.4 Export the new orchestration API from `vela_core`.

## 3. API Tests

- [x] 3.1 Add API tests that `POST /api/setup/bootstrap` returns the success aggregate on a happy path and the Web client receives the expected response shape.
- [x] 3.2 Add API tests that a failed `sync_etf_pool` step surfaces as `status=failed` with `failed_step=sync_etf_pool` and the earlier step recorded as `success`.
- [x] 3.3 Add API tests that the endpoint reuses the cached strategy config from `app.state` and does not re-read the YAML on each request.

## 4. API Implementation

- [x] 4.1 Add an API startup wiring change in `apps/api/src/vela_api/main.py` that loads the strategy config once and stores it on `app.state.strategy_config`.
- [x] 4.2 Add `POST /api/setup/bootstrap` to `apps/api/src/vela_api/main.py` that depends on the database session, the market data provider, and the cached strategy config, and calls `run_local_setup_bootstrap`.
- [x] 4.3 Serialize `BootstrapResult` to a JSON-safe response including `status`, `failed_step`, per-step `name/status/duration_seconds/error_message`, and `total_duration_seconds`.

## 5. Web Tests

- [x] 5.1 Add API client tests that `bootstrapLocalDatabase()` posts to the new endpoint and returns the parsed response.
- [x] 5.2 Add Dashboard component tests that the "Bootstrap / Setup database & data" button replaces the existing "Full fetch for initialization or repair" button.
- [x] 5.3 Add Dashboard component tests that a successful bootstrap run shows three step rows each with a success indicator plus a final total duration.
- [x] 5.4 Add Dashboard component tests that a failed bootstrap run shows the failed step with its error message and the earlier successful steps unchanged.

## 6. Web Implementation

- [x] 6.1 Add `bootstrapLocalDatabase()` to `apps/web/src/api/client.ts`.
- [x] 6.2 Update `apps/web/src/pages/DashboardPage.tsx` to replace the existing "Full fetch" button with the bootstrap action, place it at the right end of the action list, and render a three-step status display.
- [x] 6.3 Add a primary (filled) button variant in the Web styles and apply it to the bootstrap button only.
- [x] 6.4 Disable the bootstrap button while another Dashboard operation is in flight, consistent with the existing operation lock.

## 7. Verification

- [x] 7.1 Run focused core bootstrap tests.
- [x] 7.2 Run API tests for the new endpoint.
- [x] 7.3 Run Web tests for the new button and three-step status UI.
- [x] 7.4 Run the existing init-db, sync-etf-pool, and full fetch tests to confirm no regressions.
- [x] 7.5 Run `openspec status --change "2026-07-05-add-setup-bootstrap-endpoint"` and confirm the change is apply-ready.
