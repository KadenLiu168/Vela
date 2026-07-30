## Why

Vela already exercises the real strategy and backtest calculation path, but its tests do not yet prove the ingestion-to-calculation contracts in one deterministic SQLite workflow: ETF pool and calendar synchronization, controlled market-data persistence, live signal generation, backtest-owned historical signals, result persistence, and readback are covered mostly in separate tests. The existing P0 API workflow also uses weak, partly synthetic fixtures, including a legacy `positions_json` shape, so upstream/downstream drift can remain invisible until workflows are combined.

## What Changes

- Add one canonical core pipeline contract test that uses a temporary SQLite database and controlled external sources to exercise migration, ETF pool synchronization, trading-calendar synchronization, full market-data fetch, live signal generation, real backtest execution, persisted result readback, Dashboard aggregation, and real rerun isolation.
- Use deterministic official-session price series with distinguishable ETF behavior and non-trivial adjustment factors, while keeping exact financial arithmetic in focused core tests.
- Normalize shared integration fixtures so seeded backtest `positions_json` matches the production `etf_id` / `target_weight` / `actual_weight` schema.
- Refocus the P0 API workflow as a thin transport and persistence smoke test with test-owned configuration, representative data, and explicit response/serialization assertions instead of duplicating the canonical core workflow's detailed computation checks.
- Keep network-backed CLI subprocess E2E, production API changes, and changes to quant calculation behavior out of scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integration-test-data`: Require deterministic official-session price-series helpers and production-shaped backtest position fixtures reusable by the canonical core and API workflow tests.
- `test-suite-validation`: Require one canonical ingestion-to-quant core contract test and define the complementary, non-duplicative responsibilities of the P0 API smoke test.

## Impact

- Affected test support and tests: `tests/integration_data.py`, core integration tests, and `apps/api/tests/test_p0_workflow.py`.
- Existing production core, API, CLI, database, and frontend contracts remain unchanged.
- No external network access, new test framework, database migration, or dependency is introduced.
- The repository's existing pytest quality gate will collect the new and revised coverage.
