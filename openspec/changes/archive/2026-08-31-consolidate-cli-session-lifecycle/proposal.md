## Why

Ten database-backed helpers in `apps/cli/src/vela_cli/main.py` repeat the same database URL-to-managed-session wiring even though `vela_core.database.managed_session()` already owns the stable transaction lifecycle. With ECO-57 complete and ECO-59 depending on this cleanup, Vela can now consolidate that CLI-only composition without changing behavior or introducing another core database API.

## What Changes

- Add one private CLI context-managed composition boundary that creates an engine and session factory from a database URL, then delegates the session lifecycle to the existing `managed_session()` implementation.
- Route `fetch_full_market_data`, `fetch_incremental_market_data`, `sync_etf_pool`, `sync_etf_session_status`, `sync_trading_calendar`, `generate_signal`, `export_signal_report`, `run_backtest`, `run_walk_forward`, and `export_backtest_report` through that boundary.
- Keep configuration and document loading outside the managed-session scope and preserve each helper's current business call, results, errors, and engine creation frequency.
- Retain the existing core database API, transaction policy, API lifecycle, pooling behavior, and resource lifecycle without adding caching, reuse, or disposal policy.
- Exclude `init-db`, `walk-forward-worker`, schema and migration work, models, configuration schemas, CLI contracts, and later cleanup such as ECO-59.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is an internal behavior-preserving CLI wiring refactor, so no living capability requirement changes.

This change declares `skip_specs: true`; no delta spec is created.

## Impact

Implementation is limited to the private composition wiring in `apps/cli/src/vela_cli/main.py` and, only if existing regression coverage cannot protect the consolidation, a minimal CLI-local behavior test. Existing core database tests and the affected CLI suites remain the authoritative validation; no dependency, public API, database, API, Web, persisted-data, or user-visible CLI change is introduced.
