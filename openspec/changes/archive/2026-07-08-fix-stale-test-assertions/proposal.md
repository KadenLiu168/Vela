## Why

Six pytest tests are currently red on `main`, all because their assertions encode **stale snapshots of past configuration/code state** rather than the contracts those tests intend to verify. The production code and configuration are correct and internally consistent; the tests drifted behind three unrelated historical changes (ETF pool expansion `cbd85325`, `strategy_id` casing change `02c1aea8`, dashboard `etf_list` field addition `c25bfb07`). The `test-suite-validation` capability requires a passing full suite, so this debt must be cleared to restore green. Fixing it now also blocks the same drift from recurring: the corrected assertions will express contracts (loader parses yaml; `strategy_id` is passed through unchanged; dashboard `etf_list` includes the aggregated `earliest_trade_date`), not point-in-time literals.

## What Changes

- Replace hardcoded ETF-count assertions (`== 6`) in `packages/core/tests/test_config.py` and `apps/cli/tests/test_sync_etf_pool.py` with assertions derived from the loaded configuration, so they survive future pool expansions.
- Replace hardcoded `strategy_id` literal expectations (`"dual_momentum"`) in `apps/api/tests/test_dashboard.py` and `apps/api/tests/test_api_config.py` with values sourced from the loaded `AppConfig`, matching the checked-in `Dual_momentum`.
- Update the `etf_list` fixture expectations in `apps/api/tests/test_market_data_fetch.py` and `apps/api/tests/test_dashboard.py` to include the `earliest_trade_date` field that the dashboard aggregation (`dashboard_aggregation.py`, added in F-109) already produces and the frontend already consumes. The `test_dashboard.py` drift was masked behind the `strategy_id` failure and surfaces once that is fixed.
- Add a type annotation to `counts` in `packages/core/src/vela_core/strategy_signal_report.py` to resolve two pre-existing `mypy` errors (untyped `dict` built from a `Row[tuple]` query). Annotation only - no runtime behavior change.
- No configuration, database schema, API, or runtime behavior changes. No spec-level behavior changes - the behavior under test is already specified; this change only realigns tests with already-specified behavior.

## Capabilities

### New Capabilities
<!-- None: this is a test-debt cleanup that introduces no new capability. -->

### Modified Capabilities
- `test-suite-validation`: ADD a requirement formalizing that tests assert contracts (loader behavior, pass-through identity, response-shape conformance) rather than point-in-time configuration snapshots (hardcoded ETF counts, literal strategy IDs). The six red tests all violate this principle; codifying it prevents recurrence.

## Impact

- **Affected code (tests)**: `packages/core/tests/test_config.py`, `apps/cli/tests/test_sync_etf_pool.py`, `apps/api/tests/test_dashboard.py`, `apps/api/tests/test_api_config.py`, `apps/api/tests/test_market_data_fetch.py`.
- **Affected code (production, annotation-only)**: `packages/core/src/vela_core/strategy_signal_report.py` - one type annotation, no behavior change.
- **Untouched**: `config/etf_pool.yaml`, `config/strategy_v1.yaml`, `vela_api/main.py`, `vela_core/dashboard_aggregation.py`, `vela_cli/main.py`.
- **No API/DB/dependency changes**: zero runtime behavior change.
- **Out of scope**: the `strategy_id` naming convention itself (`Dual_momentum` PascalCase+snake hybrid) is noted as a separate cosmetic question and is deliberately not addressed here - production is internally consistent and renaming would cross change boundaries.
