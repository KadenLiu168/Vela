## Context

`run_local_setup_bootstrap` (`packages/core/src/vela_core/bootstrap.py`) currently runs three steps in order — `migrate` → `sync_etf_pool` → `fetch_full_market_data` — and returns a `BootstrapResult` with per-step status. The `trading_calendar` table is never populated by bootstrap, so Walk-Forward preflight (`prepare_walk_forward_inputs` in `walk_forward/preflight.py`) raises `official trading calendar has no sessions in configured range` on the first WF run, because the anchored-rolling window split queries `TradingCalendar` as the sole session axis. The user must manually run `vela sync-trading-calendar` before any WF command works, which defeats the purpose of a one-click bootstrap.

The trading calendar sync workflow already exists and is specified: `sync_trading_calendar_to_db` (`trading_calendar_sync.py`) fetches A-share trading days from akshare `tool_trade_date_hist_sina` and upserts them idempotently. On akshare failure it returns `status="failed"` with an error message rather than raising, so CLI callers can report failures without tracebacks. The `vela sync-trading-calendar` CLI command already wraps this workflow. This change wires the same workflow into the bootstrap orchestration.

Three relevant properties of the current code shape this design:

1. **Step failure semantics are not uniform.** `migrate` and `sync_etf_pool` short-circuit (return a failed `BootstrapResult` immediately on exception). `fetch_full_market_data` inspects `MarketDataFetchResult.status` and appends a failed step without short-circuiting, then lets the final `all_success` aggregate decide. This only behaves like a short-circuit today because `fetch_full_market_data` happens to be the last step.
2. **`BootstrapStepResult` carries step-specific result fields** `sync_result: ETFPoolSyncResult | None` and `fetch_result: MarketDataFetchResult | None`. A grep of the whole repo confirms neither field is ever read: the API serializer `_bootstrap_response` only emits `name`, `status`, `duration_seconds`, `error_message`, and no test accesses `step.sync_result` / `step.fetch_result`. They are effectively dead fields.
3. **`fetch_full_market_prices` does not query `trading_calendar`.** It pulls prices for active ETFs directly from the market data provider, so the calendar step and the price step have no data dependency — their relative order is a semantic choice, not a correctness constraint. The integration contract test (`test_core_pipeline_contract.py`) happens to exercise them in the order `etf_pool` → `calendar` → `prices`.

## Goals / Non-Goals

**Goals:**
- After a successful bootstrap, `trading_calendar` is populated so Walk-Forward preflight passes without a manual `vela sync-trading-calendar` step.
- The calendar step reuses the existing `sync_trading_calendar_to_db` workflow unchanged.
- The calendar step's failure mode is explicit, documented in spec, and does not silently corrupt the bootstrap result.
- The `local-setup-bootstrap` and `trading-calendar` specs reflect the four-step pipeline.

**Non-Goals:**
- Do not modify `sync_trading_calendar_to_db` itself — its failure-returns-status behavior is already correct and specified.
- Do not add a `calendar_result` field to `BootstrapStepResult`. The existing `sync_result` / `fetch_result` fields are dead (never read); adding a third would propagate the pattern. The calendar step records only `name`, `status`, `duration_seconds`, `error_message`.
- Do not clean up the dead `sync_result` / `fetch_result` fields in this change. Removing them is orthogonal to the bug fix and would expand scope; it is recorded here as a known issue for a future change.
- Do not change the frontend. The Bootstrap button already triggers `POST /api/setup/bootstrap` and the response serializer iterates `result.steps` generically, so a fourth step appears with no router/schema/frontend change.
- Do not add a schema migration. The `trading_calendar` table already exists; bootstrap simply populates it.
- Do not change the `vela sync-trading-calendar` CLI command.

## Decisions

### Decision 1: Calendar step is the third step, not the fourth

**Choice:** Order is `migrate` → `sync_etf_pool` → `sync_trading_calendar` → `fetch_full_market_data`.

**Rationale:**
- No data dependency forces a particular order (`fetch_full_market_prices` does not read `trading_calendar`), so this is a semantic/readability choice.
- The integration contract test (`test_core_pipeline_contract.py:58-69`) already exercises `etf_pool` → `calendar` → `prices`. Matching that order keeps the bootstrap pipeline and the canonical contract test aligned.
- Trading calendar is low-frequency reference metadata; market prices are high-frequency observations. Reference data before observations is the conventional layering.

**Alternative considered:** Append calendar as the fourth step (after `fetch_full_market_data`). This minimizes diff to the existing early-return logic of the first two steps but produces a pipeline where prices are fetched before the calendar that defines which sessions exist, which is harder to read and diverges from the contract test order. Rejected.

### Decision 2: Calendar step inspects status and does NOT short-circuit

**Choice:** The calendar step calls `sync_trading_calendar_to_db`, maps `result.status != "success"` to a failed `BootstrapStepResult`, appends it, and **continues** to `fetch_full_market_data`. The overall `BootstrapResult.status` is `"success"` only when all four steps succeed (existing `all_success` aggregate).

**Rationale:**
- `sync_trading_calendar_to_db` already returns `status="failed"` on akshare errors without raising, so the step mirrors the `fetch_full_market_data` failure-detection pattern (inspect status) rather than the `migrate`/`sync_etf_pool` pattern (catch exception).
- akshare is a network data source subject to temporary outages. Short-circuiting on calendar failure would prevent the user from obtaining price data that does not depend on the calendar. Not short-circuiting lets the user collect as much data as possible and surfaces the calendar failure in `failed_step` for a targeted retry.
- The `sync_etf_pool` short-circuit behavior is unchanged; this decision applies only to the calendar step. The asymmetry is documented in spec rather than hidden.

**Alternative considered:** Short-circuit on calendar failure for consistency with `migrate`/`sync_etf_pool`. Rejected because calendar sync is a flaky network operation whereas `sync_etf_pool` operates on local config data; treating them identically would make bootstrap less useful during transient akshare outages. The asymmetry is explicit and spec'd.

**Alternative considered:** Unify all steps to non-short-circuit behavior. Rejected as scope expansion — it would change `migrate` and `sync_etf_pool` behavior, which is unrelated to this bug.

### Decision 3: No new `calendar_result` field; dead fields left in place

**Choice:** The calendar step populates only `name`, `status`, `duration_seconds`, `error_message`. No `calendar_result: TradingCalendarSyncResult | None` field is added. The existing `sync_result` / `fetch_result` fields remain untouched.

**Rationale:**
- A repo-wide grep confirms `sync_result` and `fetch_result` are never read (the API serializer emits only the four generic fields; no test reads them). They are dead fields. Adding a third dead field would compound the problem.
- Removing the dead fields is orthogonal to fixing the missing-calendar-step bug. Per the project's "precise modification" principle, this change touches only what the bug requires. The dead-field cleanup is recorded as a known issue for a separate change.

**Risk:** A future contributor may still be tempted to add a step-specific result field by copy-paste. Mitigated by documenting the dead-field status here and in the spec's per-step reporting requirement, and by the code comment called out in tasks.

### Decision 4: Reuse `sync_trading_calendar_to_db` directly

**Choice:** The bootstrap step calls `sync_trading_calendar_to_db(session)` (default `source="akshare"`) with no additional arguments, identical to the CLI's call site.

**Rationale:** The function already handles import errors, call errors, parse errors, and empty-result cases by returning a failed status. Wrapping it in bootstrap-specific error handling would duplicate logic. The CLI call site (`apps/cli/src/vela_cli/main.py`) is the reference pattern.

## Risks / Trade-offs

- **[Asymmetric failure semantics] → Mitigated by spec.** The calendar step does not short-circuit while `migrate` and `sync_etf_pool` do. This is intentional (Decision 2) and is captured as an explicit scenario in `local-setup-bootstrap` spec so the asymmetry is not mistaken for a bug.
- **[Dead `sync_result`/`fetch_result` fields persist] → Accepted.** Recorded in Non-Goals and Decision 3; cleanup deferred to a separate change to keep this fix focused.
- **[Calendar coverage gap for WF range] → Out of scope.** akshare `tool_trade_date_hist_sina` returns the full historical A-share trading-day list, which covers the WF configured range (2019–2024). If a future WF range exceeds akshare's available history, that is a data-source limitation, not a bootstrap bug. The bootstrap step does not validate range coverage; preflight remains the authority on session availability.
- **[akshare transient failure on first bootstrap] → Accepted.** The user sees `failed_step="sync_trading_calendar"` with the akshare error message and can retry the endpoint or run `vela sync-trading-calendar` manually. Price data may still have been fetched, so the retry is cheaper.
- **[Default `vela.db` not migrated by this change] → Accepted.** Per project database-safety rules, no automatic migration or write to `vela.db` is performed by this change. The user runs bootstrap to populate the calendar. Validation uses test-owned `tmp_path` databases.

## Migration Plan

No schema migration. Deployment is code + spec only:

1. Merge the code change (`bootstrap.py` four-step pipeline) and spec deltas.
2. On the next `POST /api/setup/bootstrap` (or `vela`-driven bootstrap), the calendar step runs and populates `trading_calendar` for any database at the current Alembic head.
3. Existing databases with a populated `trading_calendar` are unaffected — `sync_trading_calendar_to_db` is idempotent (upsert on `trade_date` primary key).

Rollback: revert the code change. The calendar step disappears and bootstrap returns to three steps. No data cleanup needed (calendar rows remain valid).

## Open Questions

None. All design decisions are resolved above. The failure-semantics asymmetry (Decision 2) is the only judgment call and is documented in spec.
