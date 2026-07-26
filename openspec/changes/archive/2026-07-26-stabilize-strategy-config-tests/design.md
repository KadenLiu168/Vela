## Context

`apps/api/tests/test_backtest_run.py` seeds deterministic SQLite prices but lets the API load `config/strategy_v1.yaml`. The test therefore depends on two independently mutable inputs: its database fixture and the production strategy file. Its exact `max_drawdown` assertion changed when shared equity accounting changed, and production edits to momentum windows, defense assets, Top N, rebalance frequency, or costs can also invalidate the scenario.

Configuration-facing tests have the opposite responsibility: they should read the checked-in configuration and prove that it validates and is serialized faithfully. They currently mix that responsibility with hardcoded copies of mutable production values.

Focused core tests already exercise maximum-drawdown arithmetic and transaction-cost behavior with controlled `Decimal` inputs. The design must preserve those exact regression boundaries while removing their accidental duplication from an API orchestration test.

The existing `strategy-configuration` specification already requires effective parameter changes to use a new version. This Change does not redefine or automate that governance rule.

## Goals / Non-Goals

**Goals:**

- Make production strategy parameter edits independent of deterministic API backtest workflow fixtures.
- Make checked-in configuration and `/api/config` tests follow the loaded typed configuration without using the production serializer to generate both actual and expected values.
- Make API workflow metric assertions prove serialization, persistence, linkage, and domain validity.
- Preserve exact drawdown and transaction-cost regression coverage in focused core tests.
- Change only tests and OpenSpec artifacts unless implementation reveals a genuinely missing test seam.

**Non-Goals:**

- Change `config/strategy_v1.yaml`, its effective parameters, or its version.
- Introduce an active-config manifest, rename versioned configuration files, or change API/CLI default paths.
- Change strategy selection, backtest arithmetic, API response schemas, database models, or persistence.
- Make tests accept incorrect financial results by weakening focused core assertions.
- Automatically detect version reuse by comparing a configuration with Git history or an external registry.

## Decisions

### D1. Configuration-facing tests derive mutable values from typed configuration

The checked-in strategy loader test will remain a real-file smoke test, but it will assert the validated variant and structural contracts rather than copy every mutable production parameter as a literal.

The `/api/config` test will load `AppConfig` independently and construct the expected strategy object from typed model fields such as `parameters.model_dump()`, `costs.model_dump()`, `performance.model_dump()`, and `rebalance.model_dump()`.

Calling `vela_api.config._serialize_config()` to create the expected response is rejected because the same serializer produces the actual endpoint payload; using it for both sides would let a serializer defect validate itself.

### D2. API backtest execution tests inject a validated test-owned config

The two API tests that post `/api/backtests/run` will patch the symbol used by the endpoint, `vela_api.main.load_strategy_config`, to return one explicit config created through `validate_strategy_config`.

The config will fix:

- strategy id, version, and type;
- momentum, score, trend, selection, and defense inputs;
- weekly rebalance frequency;
- transaction cost and risk-free rate.

The test database will continue seeding every ETF and sufficient price history required by that config. Both the run request and the follow-up detail request will observe the same patched identity.

Adding production dependency injection solely for these tests is rejected: monkeypatching the existing imported loader is a narrow test seam and avoids changing runtime architecture.

### D3. API tests assert relationships and domain invariants, not a derived golden

The run response will be parsed as API decimal strings and compared with the persisted `BacktestRun` metrics. Maximum drawdown will additionally satisfy the engine's long-only positive-asset domain:

```text
-1 < max_drawdown <= 0
```

Signal counts and curve counts will be checked against persisted collections. A scenario-specific exact signal count may remain only where it deliberately verifies the injected weekly schedule, not the production configuration.

An exact API `max_drawdown` value is rejected because the endpoint does not calculate drawdown; it transports a core result. Pinning that value duplicates lower-level arithmetic coverage and makes legitimate engine changes look like API regressions.

### D4. Exact financial behavior remains at the core boundary

Existing core tests for deepest peak-to-trough drawdown, entry/rebalance costs, different cost rates, and cost/no-cost curves remain exact `Decimal` tests. During Apply, coverage will be traced before removing the API golden. A new core test will be added only if that trace reveals a missing contract.

Structural assertions alone are rejected for core arithmetic because `max_drawdown <= 0` cannot prove the peak-to-trough calculation, and a negative drawdown cannot prove that transaction cost was deducted.

### D5. Configuration version governance stays separate from test fixture stability

Production effective-parameter revisions must continue to use a new `version` under the existing `strategy-configuration` requirement. The deterministic test config has a test-owned identity and does not follow production version changes.

This Change does not introduce version-file immutability enforcement or a stable active-config indirection. Those mechanisms affect API, CLI, walk-forward configuration, documentation, and operational workflows and are not necessary to remove the present test coupling.

## Risks / Trade-offs

- **[Dynamic configuration expectations could become tautological]** → Build expected API values directly from independently loaded typed fields, never from the production response serializer.
- **[Removing the API golden could hide arithmetic regressions]** → Trace and retain focused exact core drawdown and transaction-cost tests before changing the API assertion.
- **[A patched loader could leak into unrelated tests]** → Scope `monkeypatch` to only the tests that execute the backtest endpoint; avoid module-wide or autouse mutation.
- **[The test config and seeded market data could diverge]** → Define the config beside the fixture and explicitly seed every configured defense asset plus sufficient lookback history.
- **[A legitimate API serialization defect could pass a non-null check]** → Compare every response metric with its persisted `BacktestRun` value and preserve exact response-shape checks.
- **[Developers may interpret dynamic config tests as permission to reuse a version]** → Keep the existing version-stability requirement explicit in proposal, design, and task verification; do not alter production YAML in this Change.

## Migration Plan

1. Add or adapt tests so configuration-facing assertions derive mutable values from independently loaded typed configuration.
2. Introduce the validated fixed strategy-config fixture and apply it only to API tests that execute backtests.
3. Replace the exact API drawdown golden with persistence equality and domain invariants.
4. Trace focused core tests for exact maximum drawdown and transaction-cost coverage, adding only a missing regression if necessary.
5. Run focused configuration, API backtest, and core equity-curve tests, then repository quality gates and strict OpenSpec validation.

Rollback consists only of reverting test and spec changes. There is no runtime deployment, schema migration, or data migration.

## Open Questions

None. Stable active-configuration indirection and automated version-history enforcement are intentionally deferred because they are broader than the observed test coupling.
