## Why

`run_local_setup_bootstrap` only runs three steps (`migrate` → `sync_etf_pool` → `fetch_full_market_data`) and never synchronizes the trading calendar. After bootstrap the `trading_calendar` table stays empty, so Walk-Forward preflight (`prepare_walk_forward_inputs`) raises `official trading calendar has no sessions in configured range` because the anchored-rolling window split uses `TradingCalendar` as the sole session axis. The bootstrap pipeline is supposed to prepare the data needed to run a WF analysis, but it leaves a required prerequisite unpopulated and forces the user to manually run `vela sync-trading-calendar` before any WF command works.

## What Changes

- Insert a fourth bootstrap step `sync_trading_calendar` between `sync_etf_pool` and `fetch_full_market_data`, invoking the existing `sync_trading_calendar_to_db` workflow (the same one the `vela sync-trading-calendar` CLI uses). Order becomes `migrate` → `sync_etf_pool` → `sync_trading_calendar` → `fetch_full_market_data`.
- Extend `StepName` to include `"sync_trading_calendar"` so `BootstrapStepResult.name` and `BootstrapResult.failed_step` type-check.
- The calendar step detects failure by inspecting `TradingCalendarSyncResult.status` (akshare fetch/parse failures return `status="failed"` without raising) and records the step status accordingly. It does **not** short-circuit: subsequent `fetch_full_market_data` still runs so the user can obtain price data even when the akshare calendar source is temporarily unavailable. The overall `BootstrapResult.status` is `"success"` only when every step succeeds, consistent with the existing aggregate contract.
- Update `local-setup-bootstrap` spec to reflect four steps, add `"sync_trading_calendar"` to the per-step name enumeration, and add scenarios for calendar-populated success and calendar-sync-failure-does-not-block-fetch.
- Add a requirement to `trading-calendar` spec documenting that the trading calendar sync is part of the bootstrap pipeline.

## Capabilities

### New Capabilities

None. The trading calendar sync workflow itself is already specified under `trading-calendar`; this change only wires it into the bootstrap orchestration.

### Modified Capabilities

- `local-setup-bootstrap`: Bootstrap now runs four steps instead of three; `StepName` gains `sync_trading_calendar`; per-step name enumeration, success/failure scenarios, and the HTTP endpoint step-count expectation all update from three to four; new scenario covers calendar sync failure not blocking the subsequent market-data fetch.
- `trading-calendar`: New requirement stating the trading calendar sync is invoked by the local setup bootstrap pipeline, with the calendar populated as a bootstrap step (reuses the already-specified sync workflow; no new sync behavior).

## Impact

- **Code**: `packages/core/src/vela_core/bootstrap.py` — import `sync_trading_calendar_to_db` + `TradingCalendarSyncResult`, extend `StepName`, add the fourth step block. No change to `sync_trading_calendar_to_db` itself.
- **API**: `POST /api/setup/bootstrap` response gains a fourth entry in `steps` with `name="sync_trading_calendar"`. The `_bootstrap_response` serializer already iterates `result.steps` generically (it does not read step-specific result fields), so no router/schema change is needed. Frontend already triggers the endpoint and renders the steps list generically — zero frontend change.
- **CLI**: `vela sync-trading-calendar` is unaffected; it remains the standalone manual entry point.
- **Specs**: `openspec/specs/local-setup-bootstrap/spec.md` (six hardcoded "three steps" references + new scenario), `openspec/specs/trading-calendar/spec.md` (new bootstrap-integration requirement).
- **Tests**: Extend bootstrap unit tests to assert four steps including `sync_trading_calendar`, calendar-empty fixture becomes non-empty after bootstrap, and calendar-sync-failure does not block `fetch_full_market_data` while still marking the overall result failed.
- **Data**: No schema migration; `trading_calendar` table already exists. Default `vela.db` gains rows on the next bootstrap run; no automatic migration is performed by this change.
