## 1. Deterministic Integration Support

- [x] 1.1 Add integration-data regressions requiring `ControlledMarketDataProvider` to record `(symbol, start_date, end_date)`, filter returned rows to the inclusive requested range, and keep incremental expectations independent of the wall clock; update every dependent provider-request assertion to the complete tuple contract.
- [x] 1.2 Add the minimal reusable official-session, short-window test config/pool, and distinguishable price-series helpers in `tests/integration_data.py`; use a constant non-unit factor on one known-unselected series and verify the fixture uses no randomness, current dates, or network access.
- [x] 1.3 Add a regression that decodes the shared equity-curve fixture's `positions_json` and requires the production `etf_id`, `target_weight`, and `actual_weight` decimal-string shape.
- [x] 1.4 Normalize the shared equity-curve fixture and update only its dependent fixture assertions, preserving local opaque-text pass-through tests that do not claim to model production positions.

## 2. Canonical Core Pipeline Contract

- [x] 2.1 Add one canonical core test that runs Alembic upgrade to head against a `tmp_path` SQLite file without calling ORM `create_all`, creates the engine/session factory only afterward, injects an ISO-string DataFrame through `monkeypatch.setitem(sys.modules, "akshare", fake)`, and runs real ETF pool sync, calendar sync, and full fetch through separate managed sessions that assert successful results before committing.
- [x] 2.2 In fresh read/service sessions, verify active membership, complete official-session coverage, full-fetch request bounds, fetch-log persistence, and raw `close_price`/constant non-unit `factor_hfq` precision before extending the scenario through the real live signal service and real backtest runner without replacing strategy generation, equity calculation, or metric calculation.
- [x] 2.3 Assert deterministic selected identities, rank/weight invariants, production-shaped curve positions, manual-vs-backtest provenance, persisted run/signal linkage, backtest result readback, and Dashboard latest-successful/recent-run/fetch linkage using production ordering.
- [x] 2.4 Run the same config and date range a second time in a new caller-managed transaction; prove disjoint linked signal IDs, unchanged first-run signals/curve/metrics/snapshot, equality of both complete `data_snapshot_json` values and checksums, and independent readback of both runs.

## 3. P0 API Smoke Refinement

- [x] 3.1 Inventory every existing `test_p0_workflow.py` endpoint call and assertion before editing; label each item retain, rewrite-as-derived-invariant, or remove-as-duplicated, preserving provider symbol ordering and all unique HTTP/read-after-write evidence.
- [x] 3.2 Refactor `apps/api/tests/test_p0_workflow.py` to inject a validated short-window test-owned strategy configuration, reuse representative official-session integration data, fix `market_data_fetcher._today()`, and preserve the existing real endpoint sequence.
- [x] 3.3 Assert complete provider request bounds, HTTP response contracts, persisted-value readback, manual signal identity/rank/weight/provenance, production-shaped equity-curve positions, trading-day and signal counts derived from controlled sessions/linked collections, and Dashboard linkage under production latest-signal ordering; remove only assertions classified as duplicated in task 3.1.

## 4. Validation

- [x] 4.1 Run the integration-data, canonical core pipeline, P0 API workflow, and directly affected backend test modules and resolve all failures without weakening assertions.
- [x] 4.2 Run the complete Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, `uv run --no-sync pytest`, and `git diff --check`.
- [x] 4.3 Run strict OpenSpec validation for `strengthen-core-quant-pipeline-contract-tests` and confirm the completed implementation changes only test support, tests, and this Change's artifacts.
