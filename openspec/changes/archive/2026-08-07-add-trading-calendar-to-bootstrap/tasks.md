## 1. Bootstrap pipeline code

- [x] 1.1 In `packages/core/src/vela_core/bootstrap.py`, extend `StepName` to `Literal["migrate", "sync_etf_pool", "sync_trading_calendar", "fetch_full_market_data"]`.
- [x] 1.2 Add imports for `sync_trading_calendar_to_db` and `TradingCalendarSyncResult` from `vela_core.trading_calendar_sync`.
- [x] 1.3 Insert the `sync_trading_calendar` step between `sync_etf_pool` and `fetch_full_market_data`: call `sync_trading_calendar_to_db(session)`, map `result.status != "success"` to `BootstrapStepResult(status="failed", error_message=result.error_message)`, append the step, and DO NOT short-circuit (continue to `fetch_full_market_data`). Do not add a `calendar_result` field to `BootstrapStepResult`.
- [x] 1.4 Add a brief code comment noting that `sync_result`/`fetch_result` fields on `BootstrapStepResult` are currently unread (see design.md Decision 3) so future steps should not add step-specific result fields.

## 2. Unit tests

- [x] 2.1 Extend the bootstrap unit test to assert `run_local_setup_bootstrap` returns exactly four steps in order: `migrate`, `sync_etf_pool`, `sync_trading_calendar`, `fetch_full_market_data`, all with `status="success"` and `failed_step=None`. Use the akshare mock pattern from `test_core_pipeline_contract.py:48-52` (`ModuleType("akshare")` + `monkeypatch.setitem(sys.modules, ...)`).
- [x] 2.2 Add a test: against a fixture with an empty `trading_calendar` table, after a successful bootstrap the `trading_calendar` table has more than zero rows.
- [x] 2.3 Add a test for calendar sync failure: mock akshare to raise (or return an empty frame) so `sync_trading_calendar_to_db` returns `status="failed"`, then assert the `sync_trading_calendar` step has `status="failed"` with a populated `error_message`, the `fetch_full_market_data` step STILL executes (records its own status), and the overall `BootstrapResult` has `status="failed"` and `failed_step="sync_trading_calendar"`.
- [x] 2.4 Add a test for re-run idempotency: bootstrap against a database that already has trading days synced; assert the `sync_trading_calendar` step reports `status="success"` and the calendar row count does not duplicate.

## 3. Spec artifacts (already drafted, finalize during implementation)

- [x] 3.1 Confirm `openspec/specs/local-setup-bootstrap/spec.md` delta (four-step pipeline, `sync_trading_calendar` in name enumeration, three→four in HTTP scenario, calendar-failure-does-not-block-fetch requirement) matches the implemented behavior.
- [x] 3.2 Confirm `openspec/specs/trading-calendar/spec.md` delta (bootstrap-integration requirement) matches the implemented call site.

## 4. Verification

- [x] 4.1 Run `openspec validate add-trading-calendar-to-bootstrap --strict` and confirm it passes.
- [x] 4.2 Run the targeted bootstrap tests: `uv run --no-sync pytest packages/core/tests -k bootstrap` (adjust path to the actual bootstrap test file).
- [x] 4.3 Run the full Python gate per `AGENTS.md`: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, `uv run --no-sync pytest`.
- [x] 4.4 Confirm `POST /api/setup/bootstrap` endpoint test (`apps/api/tests/test_bootstrap_endpoint.py`) still passes without router/schema changes — the serializer iterates `result.steps` generically so a fourth step requires no endpoint edit. If any endpoint test hardcodes a step count, update it to four.
